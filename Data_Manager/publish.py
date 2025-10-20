import json
import os
import hashlib
from time import sleep
from celery import shared_task
from django.http import HttpResponse, JsonResponse
from . import instagram_session
from instagrapi.exceptions import ClientConnectionError, ChallengeRequired
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from pymongo.errors import DuplicateKeyError
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import requests
from env import get
from . import mongo_session
from . import text_ai
from datetime import datetime, timedelta
from . import minio_session
from urllib3.exceptions import ResponseError
from bson import json_util
import openai
import logging
from .text_ai import news_data
import json as jsonloader
from . import telegram_publish
from dotenv import load_dotenv
import traceback
import uuid

# Load environment variables
load_dotenv()

# Get proxy configuration from environment variables
PROXY_USERNAME = os.getenv('PROXY_USERNAME')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD')
PROXY_HOST = os.getenv('PROXY_HOST')
PROXY_PORT = os.getenv('PROXY_PORT')

# Construct proxy URL
PROXY_URL = f"socks5://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"

from instagrapi import Client

logger = logging.getLogger(__name__)

db = mongo_session.get_mongo_session()
collection = db["Published"]
queue_collection = db["Queue"]
queue_error_collection = db["Queue_Errors"]
instagram_session_collection = db["instagram_session"]
telegram_channel_collection = db["telegram_channels"]
bucket_name = 'josef'
SERVER = get('SERVER')
minio_client = minio_session.get_minio_session()

insta = instagram_session.get_insta_clients()
print(f"This is insta sessions: {insta}")
queue_error_collection.create_index([("id", 1)], unique=True)
queue_collection.create_index([("id", 1)], unique=True)
prompt_collection = db["master_prompt"]

# ---- NEW: locks collection for idempotency (unique per queue_id/account/type) ----
locks_collection = db["PublishLocks"]
try:
    locks_collection.create_index([("key", 1)], unique=True)
    # Optional TTL so stale locks clear automatically (1 hour)
    locks_collection.create_index("expireAt", expireAfterSeconds=0)
except Exception as _e:
    logger.warning(f"Lock index creation warning: {_e}")

OPclient = openai.OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# -----------------------------
# Helpers
# -----------------------------

def find_session(username):
    """Return the instagrapi session for a given username, or None."""
    for u, s in insta:
        if u == username:
            return s
    return None

def acquire_publish_lock(queue_id: int, account: str, media_type: str, ttl_seconds: int = 3600) -> bool:
    """
    Acquire a per-(queue_id, account, media_type) publish lock.
    Returns True if acquired, False if already held (idempotency guard).
    """
    key = f"{queue_id}:{account}:{media_type}"
    try:
        locks_collection.insert_one({
            "key": key,
            "createdAt": datetime.utcnow(),
            "expireAt": datetime.utcnow() + timedelta(seconds=ttl_seconds),
            "token": str(uuid.uuid4())
        })
        return True
    except DuplicateKeyError:
        return False

def already_published(document_id: int, account_name: str, media_type: str) -> bool:
    """
    Check queue document to see if this media_type has already succeeded for the account.
    (Reels map to post_status on the front-end.)
    """
    doc = queue_collection.find_one({"id": int(document_id)}, {"accounts": 1})
    if not doc:
        return False
    for acc in doc.get("accounts", []):
        if acc.get("username") != account_name:
            continue
        if media_type == "story":
            return acc.get("story_status") is True
        # post or reels use post_status bucket
        return acc.get("post_status") is True
    return False

def make_reels_client(session_json):
    """
    Build an isolated instagrapi.Client for reels publishing.
    Avoids cross-talk from a global client.
    """
    c = Client()
    c.set_proxy(PROXY_URL)
    if session_json:
        c.set_settings(session_json)
    return c

# -----------------------------
# Tasks / Views
# -----------------------------

@shared_task
def automate_post(country, account):
    """
    Disabled as the news feature is no longer used.
    """
    try:
        description, hashtags = description_hashtags(account, "both")
        doc = telegram_channel_collection.find_one({"insta": account})
        message = "The news feature has been disabled as per user request."
        print(message)
        for username, session in insta:
            if username == account:
                print(f"Attempted to use news feature for account: {account}")
                break
        return {"status": "disabled", "message": message}
    except Exception as e:
        print(str(e))
        return {"status": "error", "message": str(e)}

@login_required
def clients(request):
    clients = []
    for session in insta:
        username = session.account_info().username
        try:
            clients.append(username)
        except ChallengeRequired:
            instagram_session.unhealthy(username, "ChallengeRequired")
            continue
    return JsonResponse({'message': clients}, status=200)

def get_next_id(collection):
    result = collection.find_one({}, sort=[("id", -1)])
    if result and 'id' in result:
        return result['id'] + 1
    else:
        return 1000  # Start from 1000 if collection is empty

# Configure logging
logger = logging.getLogger(__name__)
temp_dir = '/tmp'

@login_required
@api_view(['POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def publish_content(request):
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H%M%S")
    username = request.user.username
    generated = False
    temp_image_path = None
    object_name = None
    next_id = get_next_id(queue_collection)
    try:
        # Django request object is already parsed in DRF
        logger.debug(f"Request user: {username}")

        image = request.POST.get('image_url')
        types = json.loads(request.POST.get('types', '[]'))
        accounts_raw = json.loads(request.POST.get('accounts', '[]'))
        # ---- NEW: de-duplicate accounts to avoid double publishing same user ----
        accounts = list(dict.fromkeys(accounts_raw))
        caption = request.POST.get('caption')
        time_gap = request.POST.get('time_gap') or "0"

        print(f"These are accounts: {accounts}")

        if not image:
            # Handle file upload case
            photo_file = request.FILES.get('photo')
            print(f"This is photo name: {photo_file}")
            if photo_file:
                filename = photo_file.name
                object_name = f"{filename.split('.')[0]}_{formatted_time}.{filename.split('.')[-1]}"
                temp_image_path = os.path.join(temp_dir, object_name)
                with open(temp_image_path, 'wb') as temp_image:
                    for chunk in photo_file.chunks():
                        temp_image.write(chunk)

                # Upload to Minio
                try:
                    minio_client.fput_object(bucket_name, object_name, temp_image_path)
                except ResponseError as error:
                    return JsonResponse({"error": "Failed to save image in Minio!"}, status=500)
            else:
                return JsonResponse({"error": "No file uploaded!"}, status=400)

        temp_cover_path = None
        if 'reels' in types:
            cover = request.FILES.get('cover')
            if cover:
                print(f"This is cover name: {cover.name}")
                filename = cover.name
                object_name_cover = f"{filename.split('.')[0]}_{formatted_time}.{filename.split('.')[-1]}"
                temp_cover_path = os.path.join(temp_dir, object_name_cover)
                with open(temp_cover_path, 'wb') as temp_image:
                    for chunk in cover.chunks():
                        temp_image.write(chunk)
                minio_client.fput_object(bucket_name, object_name_cover, temp_cover_path)
            else:
                print("No cover file uploaded!")

        elif image:
            # Handle image URL case
            print("here?")
            image_url = image
            print(f"this is image url: {image_url}")
            response = requests.get(image_url)
            if response.status_code == 200:
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                hashed_name = hashlib.md5(image_url.encode('utf-8')).hexdigest()
                file_extension = os.path.splitext(image_url)[1]
                sanitized_object_name = f"{hashed_name}{file_extension}"
                temp_image_path = os.path.join(temp_dir, sanitized_object_name)
                with open(temp_image_path, 'wb') as temp_image:
                    temp_image.write(response.content)
                object_name = f"{next_id}_{formatted_time}.{image_url.split('.')[-1]}"
                minio_client.fput_object(bucket_name, object_name, temp_image_path)
                print(f"Image saved successfully at: {temp_image_path}")
            else:
                return JsonResponse({"error": "Failed to download the image."}, status=400)

        # Prepare doc for MongoDB
        document = {
            "id": next_id,
            "username": username,
            "timestamp": formatted_time,
            "path": object_name if image else object_name,  # ensure object_name exists from above
            "types": types,
            "caption": caption,
            "generated": True,
            "time_gap": time_gap,
            "cover": temp_cover_path,
            "accounts": [
                {
                    "username": account,
                    "description": description_hashtags(account, "description"),
                    "hashtags": description_hashtags(account, "hashtags"),
                    "lastCheck": formatted_time
                } for account in accounts
            ],
            "active": True
        }

        # Initialize per-type fields
        for acc in document["accounts"]:
            if "story" in types:
                acc["story_status"] = None
                acc["story_message"] = "Not started."
            if "post" in types or "reels" in types:
                # Use post_* fields for both post and reels (front-end expects post_*).
                acc["post_status"] = None
                acc["post_message"] = "Not started."

        # Insert into DB
        try:
            result = queue_collection.insert_one(document)
            if not result.inserted_id:
                return JsonResponse({"error": "Failed to insert document in DB."}, status=500)
        except DuplicateKeyError:
            return JsonResponse({"error": "Duplicate path found in the database. Path must be unique."}, status=400)

        # Trigger celery task (keep existing orchestration; tasks are now safe/idempotent)
        if "reels" in types:
            if temp_cover_path:
                queue.delay(time_gap, accounts, types, caption, temp_image_path, document["id"], temp_cover_path)
            else:
                queue_notcover.delay(time_gap, accounts, types, caption, temp_image_path, document["id"])
        elif "post" in types:
            queue_notcover.delay(time_gap, accounts, types, caption, temp_image_path, document["id"])
        else:
            queue.delay(time_gap, accounts, types, caption, temp_image_path, document["id"], None)

        return JsonResponse({"message": "Task triggered successfully!"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format in request body."}, status=400)
    except Exception as e:
        logger.error("Unhandled exception in publish_content:\n" + traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)

def pub(type, id, account, session, caption, image, cover=None):
    """
    Unified publisher for story/post/reels. 'cover' is optional.
    NOTE: Reels uses an isolated Client per publish to avoid cross-talk.
    """
    if type == "story":
        try:
            session.photo_upload_to_story(image)
            update_status("story", id, account, True, "", "")
            return
        except ClientConnectionError:
            update_status("story", id, account, False, "ClientConnectionError", "")
            raise
        except Exception as e:
            update_status("story", id, account, False, str(e), "")
            raise

    if type == "post":
        try:
            session.set_proxy(PROXY_URL)
            session.photo_upload(image, caption)
            update_status("post", id, account, True, "", caption)
            return
        except ClientConnectionError:
            update_status("post", id, account, False, "ClientConnectionError", caption)
            raise
        except Exception as e:
            update_status("post", id, account, False, str(e), caption)
            raise

    if type == "reels":
        try:
            session_record = instagram_session_collection.find_one({"username": account})
            session_json = session_record.get("session_json") if session_record else None
            # ---- NEW: per-publish client ----
            reel_client = make_reels_client(session_json)
            # Upload reel
            if cover:
                reel_client.clip_upload(image, caption, cover)
            else:
                reel_client.clip_upload(image, caption)
            update_status("reels", id, account, True, "", caption)
            return
        except ClientConnectionError:
            update_status("reels", id, account, False, "ClientConnectionError", caption)
            raise
        except Exception as e:
            update_status("reels", id, account, False, str(e), caption)
            raise

def pub_reels_withoutcover(type, id, account, session, caption, image):
    if type == "story":
        try:
            session.photo_upload_to_story(image)
            update_status("story", id, account, True, "", "")
            return
        except ClientConnectionError:
            update_status("story", id, account, False, "ClientConnectionError", "")
            raise
        except Exception as e:
            update_status("story", id, account, False, str(e), "")
            raise

    if type == "post":
        try:
            session.set_proxy(PROXY_URL)
            session.photo_upload(image, caption)
            update_status("post", id, account, True, "", caption)
            return
        except ClientConnectionError:
            update_status("post", id, account, False, "ClientConnectionError", caption)
            raise
        except Exception as e:
            update_status("post", id, account, False, str(e), caption)
            raise

    if type == "reels":
        try:
            session_record = instagram_session_collection.find_one({"username": account})
            session_json = session_record.get("session_json") if session_record else None
            # ---- NEW: per-publish client ----
            reel_client = make_reels_client(session_json)
            # Optional warm-up (can be omitted):
            # reel_client.get_timeline_feed()
            reel_client.clip_upload(image, caption)
            update_status("reels", id, account, True, "", caption)
            return
        except ClientConnectionError:
            update_status("reels", id, account, False, "ClientConnectionError", caption)
            raise
        except Exception as e:
            update_status("reels", id, account, False, str(e), caption)
            raise

# ---- IMPORTANT: acks_late=False to avoid redelivery after long sleeps ----
@shared_task(bind=True, acks_late=False)
def queue(self, gap, accounts, types, caption, image, id, cover, null="null"):
    """
    Orchestrates story/post/reels for multiple accounts with a gap between each.
    Changes:
      - acks_late=False to reduce duplicate redelivery after upload but before ack.
      - reels protected with an idempotency lock.
      - skip if already published (extra safety).
    """
    print(f"Arguments received: {gap}, {accounts}, {types}, {caption}, {image}, {id}, {cover}")
    gap_int = int(gap)
    gap_seconds = gap_int * 60

    for account in accounts:
        session = find_session(account)
        if not session:
            logger.error(f"No session found for account {account}")
            # Mark both story/post (and reels mapped to post) as failed for visibility
            if "story" in types:
                update_status("story", id, account, False, "No session", "")
            if "post" in types or "reels" in types:
                update_status("post", id, account, False, "No session", caption)
            sleep(gap_seconds)
            continue

        # STORY
        if "story" in types:
            try:
                if not already_published(id, account, "story"):
                    pub("story", id, account, session, caption, image)
                else:
                    logger.info(f"[skip duplicate] story already published id={id} account={account}")
            except Exception as e:
                logger.exception(f"Story publish failed for {account}: {e}")

        # POST
        if "post" in types:
            try:
                if not already_published(id, account, "post"):
                    if "aicaption" in types:
                        description, hashtags = description_hashtags(account, "both")
                        private_caption = get_caption(account, caption, description, hashtags, id)
                        pub("post", id, account, session, private_caption, image)
                    else:
                        pub("post", id, account, session, caption, image)
                else:
                    logger.info(f"[skip duplicate] post already published id={id} account={account}")
            except Exception as e:
                logger.exception(f"Post publish failed for {account}: {e}")

        # REELS
        if "reels" in types:
            try:
                # ---- NEW: idempotency lock just for reels ----
                if not already_published(id, account, "reels") and acquire_publish_lock(id, account, "reels"):
                    if "aicaption" in types:
                        description, hashtags = description_hashtags(account, "both")
                        private_caption = get_caption(account, caption, description, hashtags, id)
                        pub("reels", id, account, session, private_caption, image, cover)
                    else:
                        pub("reels", id, account, session, caption, image, cover)
                else:
                    logger.info(f"[skip duplicate] reels already published/locked id={id} account={account}")
            except Exception as e:
                logger.exception(f"Reels publish failed for {account}: {e}")

        # Wait between accounts
        sleep(gap_seconds)

    try:
        if os.path.exists(image):
            os.remove(image)
    except Exception as e:
        logger.warning(f"Could not remove temp image {image}: {e}")
    trigger_status(False, id)

@shared_task(bind=True, acks_late=False)
def queue_notcover(self, gap, accounts, types, caption, image, id, null="null"):
    print(f"Arguments received: {gap}, {accounts}, {types}, {caption}, {image}, {id}")
    gap_int = int(gap)
    gap_seconds = gap_int * 60

    for account in accounts:
        session = find_session(account)
        if not session:
            logger.error(f"No session found for account {account}")
            if "story" in types:
                update_status("story", id, account, False, "No session", "")
            if "post" in types or "reels" in types:
                update_status("post", id, account, False, "No session", caption)
            sleep(gap_seconds)
            continue

        # STORY
        if "story" in types:
            try:
                if not already_published(id, account, "story"):
                    pub("story", id, account, session, caption, image)
                else:
                    logger.info(f"[skip duplicate] story already published id={id} account={account}")
            except Exception as e:
                logger.exception(f"Story publish failed for {account}: {e}")

        # POST
        if "post" in types:
            try:
                if not already_published(id, account, "post"):
                    if "aicaption" in types:
                        description, hashtags = description_hashtags(account, "both")
                        private_caption = get_caption(account, caption, description, hashtags, id)
                        pub("post", id, account, session, private_caption, image)
                    else:
                        pub("post", id, account, session, caption, image)
                else:
                    logger.info(f"[skip duplicate] post already published id={id} account={account}")
            except Exception as e:
                logger.exception(f"Post publish failed for {account}: {e}")

        # REELS (without cover)
        if "reels" in types:
            try:
                if not already_published(id, account, "reels") and acquire_publish_lock(id, account, "reels"):
                    if "aicaption" in types:
                        description, hashtags = description_hashtags(account, "both")
                        private_caption = get_caption(account, caption, description, hashtags, id)
                        pub_reels_withoutcover("reels", id, account, session, private_caption, image)
                    else:
                        pub_reels_withoutcover("reels", id, account, session, caption, image)
                else:
                    logger.info(f"[skip duplicate] reels already published/locked id={id} account={account}")
            except Exception as e:
                logger.exception(f"Reels publish failed for {account}: {e}")

        sleep(gap_seconds)

    try:
        if os.path.exists(image):
            os.remove(image)
    except Exception as e:
        logger.warning(f"Could not remove temp image {image}: {e}")
    trigger_status(False, id)

def update_status(type, document_id, account_name, status, e="", caption=""):
    """
    Fixes:
    - Uses correct messages: "Published!" on success, error text on failure.
    - Accepts caption default to avoid older calls breaking.
    - Maps 'reels' to post_* fields for front-end compatibility.
    """
    rec_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if type == "story":
        index = "story_status"
        message = "story_message"
    elif type == "post" or type == "reels":
        index = "post_status"
        message = "post_message"
    else:
        index = "post_status"
        message = "post_message"

    document_id = int(document_id)
    document = queue_collection.find_one({"id": document_id})
    if not document:
        return

    # Success
    if status is True:
        update_doc = {
            f"accounts.$.{index}": True,
            f"accounts.$.{message}": "Published!",
            "accounts.$.lastCheck": rec_time
        }
        if type == "post" or type == "reels":
            update_doc["accounts.$.caption"] = caption
        try:
            queue_collection.update_one(
                {"id": document_id, "accounts.username": account_name},
                {"$set": update_doc}
            )
        except Exception as err:
            logger.error(str(err))
        return

    # Failure (False) or transitional (None)
    update_doc = {
        f"accounts.$.{index}": status,
        f"accounts.$.{message}": e,
        "accounts.$.lastCheck": rec_time
    }
    if type == "post" or type == "reels":
        update_doc["accounts.$.caption"] = caption

    try:
        queue_collection.update_one(
            {"id": document_id, "accounts.username": account_name},
            {"$set": update_doc}
        )
    except Exception as err:
        logger.error(str(err))

    try:
        if str(e) == '{"message":"login_required","status":"fail"}':
            instagram_session_collection.update_one(
                {"username": account_name},
                {"$set": {"status": "unHealthy", "lastCheck": rec_time}}
            )
    except Exception as err:
        logger.error(f"Failed to update instagram_session status for {account_name}: {err}")

# @login_required
def queue_log(request):
    parts_list = []
    username = "admin"
    document = queue_collection.find({"username": username})
    if document:
        for doc in document:
            id = doc.get('id')
            image = doc.get('path')
            timestamp = doc.get('timestamp')
            caption = doc.get('caption')
            true_count = 0
            false_count = 0
            none_count = 0
            types = doc.get("types", [])

            post_check = "post" in types or "reels" in types  # count reels in post bucket
            story_check = "story" in types

            for account in doc.get('accounts', []):
                story_status = account.get('story_status')
                post_status = account.get('post_status')

                if story_check:
                    if story_status is True:
                        true_count += 1
                    elif story_status is False:
                        false_count += 1
                    else:
                        none_count += 1

                if post_check:
                    if post_status is True:
                        true_count += 1
                    elif post_status is False:
                        false_count += 1
                    else:
                        none_count += 1

            Err = false_count > 0

            if post_check and story_check:
                odd = 2
            else:
                odd = 1

            total_count = len(doc.get('accounts', []))
            j2 = {
                "id": id,
                "image": image,
                "timestamp": timestamp,
                "caption": caption,
                "account_count": total_count,
                "Error": Err,
                "true_percentage": int((true_count / (max(total_count * odd, 1))) * 100)
            }
            parts_list.append(j2)

        return JsonResponse(parts_list, safe=False, status=200)
    else:
        return JsonResponse({'message': 'No such a log in db.'}, status=404)

# @login_required
@csrf_exempt
def queue_d(request):
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    id = body_data.get('id')

    username = request.user.username
    doc = queue_collection.find_one({"id": id})
    if doc:
        id = doc.get('id')
        image = doc.get('path')
        timestamp = doc.get('timestamp')
        caption = doc.get('caption')
        true_count = 0
        false_count = 0
        none_count = 0

        for account in doc.get('accounts', []):
            story_status = account.get('story_status')
            post_status = account.get('post_status')
            post_message = account.get('post_message')
            story_message = account.get('story_message')
            active = account.get('active')

            if story_status is True:
                true_count += 1
            elif story_status is False:
                false_count += 1
            else:
                none_count += 1

            if post_status is True:
                true_count += 1
            elif post_status is False:
                false_count += 1
            else:
                none_count += 1

            account['post_message'] = post_message
            account['story_message'] = story_message

        Err = false_count > 0
        total_count = len(doc.get('accounts', []))
        j2 = {
            "id": id,
            "image": image,
            "timestamp": timestamp,
            "account_count": total_count,
            "caption": caption,
            "Error": Err,
            "true_percentage": int((true_count / (max(total_count * 2, 1))) * 100),
            "accounts": doc.get('accounts', []),
            "active": active
        }

        return JsonResponse(j2, safe=False)
    else:
        return JsonResponse({'error': 'Document not found'}, status=404)

@csrf_exempt
def queue_retry_data(request):
    arr = []
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)
    id = int(body_data.get('id'))
    doc = queue_collection.find_one({"id": id})
    if doc.get("active"):
        return JsonResponse({"error": "The task is triggered on the document!"}, status=500)

    trigger_status(True, id)
    gap = doc.get('time_gap') or "0"
    image = doc.get('path')
    caption = doc.get('caption')

    temp_dir = '/tmp'
    image_url = f"http://{SERVER}/image/" + image

    response = requests.get(image_url)
    if response.status_code == 200:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        temp_image_path = os.path.join(temp_dir, 'temp_image.jpg')
        with open(temp_image_path, 'wb') as temp_image:
            temp_image.write(response.content)
    else:
        return JsonResponse({"error": "Failed to download the image."}, status=400)

    if doc:
        accounts = doc.get('accounts', [])
        for account in accounts:
            username = account.get('username')
            story_status = account.get('story_status')
            post_status = account.get('post_status')

            account_issues = [username]
            if story_status is None or story_status is False:
                account_issues.append('story')
            if post_status is None or post_status is False:
                account_issues.append('post')

            if len(account_issues) > 1:
                arr.append(account_issues)

    queue_retry.delay(arr, id, temp_image_path, gap, caption)
    return JsonResponse({"message": "Task triggered successfully!"})

@shared_task(bind=True, acks_late=False)
def queue_retry(self, status_arr, id, image, gap, caption):
    gap = int(gap or 0) * 60
    for account in status_arr:
        account_len = int(len(account))
        session = find_session(account[0])
        if not session:
            update_status("story", id, account[0], False, "No session", "")
            update_status("post", id, account[0], False, "No session", caption)
            sleep(gap)
            continue

        for i in range(1, account_len):
            if account[i] == "story":
                try:
                    if not already_published(id, account[0], "story"):
                        update_status("story", id, account[0], None, "retrying!")
                        pub("story", id, account[0], session, caption, image)
                    else:
                        logger.info(f"[retry skip] story already published id={id} account={account[0]}")
                except Exception:
                    logger.exception(f"Retry story failed for {account[0]}")
            if account[i] == "post":
                try:
                    if not already_published(id, account[0], "post"):
                        update_status("post", id, account[0], None, "retrying!", caption)
                        pub("post", id, account[0], session, caption, image)
                    else:
                        logger.info(f"[retry skip] post already published id={id} account={account[0]}")
                except Exception:
                    logger.exception(f"Retry post failed for {account[0]}")

        sleep(gap)

    try:
        if os.path.exists(image):
            os.remove(image)
    except Exception as e:
        logger.warning(f"Could not remove temp image {image}: {e}")
    trigger_status(False, id)

# @login_required
def delete_queue(request, id):
    username = request.user.username
    document = queue_collection.find_one({"id": id})
    if document:
        if document.get('username') == username:
            try:
                queue_collection.delete_one({"id": id})
                return JsonResponse({'error': 'Queue deleted successfully.'}, status=200)
            except Exception as err:
                return JsonResponse({'error': 'An error has occurred while updating db.'}, status=400)
        return JsonResponse({'error': 'You are not allowed to delete this queue.'}, status=401)
    else:
        return JsonResponse({'error': 'No such queue in db.'}, status=404)

def trigger_status(status, id):
    queue_collection.update_one(
        {"id": id},
        {"$set": {"active": status}}
    )

def description_hashtags(username, mode):
    document = instagram_session_collection.find_one({"username": username})
    if mode == "description":
        return document.get("description")
    if mode == "hashtags":
        return document.get("hashtags")
    else:
        hashtags = document.get("hashtags")
        description = document.get("description")
        return description, hashtags

def run_gpt(account_name, caption, description, hashtags, queue_id):
    """
    Generate an Instagram caption + exactly 15 hashtags.

    Params:
        account_name (str)
        caption (str): keywords about the picture/content
        description (str): account bio/summary (optional context)
        hashtags (str | list[str]): related hashtags or keywords (optional context)
        queue_id (Any)

    Returns:
        str: caption text followed by 15 hashtags (no labels)
    """
    try:
        import os
        from openai import OpenAI

        # Use an existing global client if you've created one elsewhere,
        # otherwise create a local client.
        client = globals().get("OPclient") or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Normalize optional context
        ctx_hashtags = ", ".join(hashtags) if isinstance(hashtags, (list, tuple)) else (hashtags or "")
        ctx_description = description or ""

        user_caption_prompt = (
            "Write a caption for my personal Instagram post.\n"
            f"Picture keywords: {caption}\n"
            f"Account context: {account_name}\n"
            f"About the account: {ctx_description}\n"
            f"Related hashtags/keywords (context only, not to copy verbatim): {ctx_hashtags}\n\n"
            "Output requirements:\n"
            "- Friendly second-person tone (“you”), catchy/viral vibe.\n"
            "- After the caption text, include exactly 15 hashtags.\n"
            "- The first 4 hashtags: low-competition AND directly related to the picture keywords.\n"
            "- The next 7 hashtags: low-competition (relevant).\n"
            "- The next 4 hashtags: medium-competition.\n"
            "- The last 2 hashtags: high-competition.\n"
            "- Do NOT label or explain anything. Output only the caption text and the hashtags.\n"
        )

        # Chat Completions (keeps your original structure, updated model/imports)
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Instagram caption writer. "
                               "Return only the caption text followed by 15 hashtags."
                },
                {"role": "user", "content": user_caption_prompt},
            ],
            temperature=0.8,
        )

        return resp.choices[0].message.content.strip()

    except Exception as e:
        # keep your existing error side-effect
        update_status("post", queue_id, account_name, False, str(e), "")
        raise

def run_gpt_news(account_name, caption, description, hashtags, queue_id):
    return run_gpt(account_name, caption, description, hashtags, queue_id)

def get_caption(account_name, caption, description, hashtags, queue_id):
    """
    Fixed parameter order usage across the code:
    get_caption(account, caption, description, hashtags, id)
    """
    caption_text = run_gpt(account_name, caption, description, hashtags, queue_id)
    caption_text = caption_text.replace("Caption:", "").replace("CAPTION:", "").replace('"', "").strip()
    return caption_text

def get_caption_news(account_name, caption, description, hashtags, queue_id):
    return get_caption(account_name, caption, description, hashtags, queue_id)
