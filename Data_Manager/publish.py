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
from datetime import datetime
from . import minio_session
from urllib3.exceptions import ResponseError
from bson import json_util
import openai
import logging
from .text_ai import news_data
import json as jsonloader
from . import telegram_publish
from dotenv import load_dotenv

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

cl = Client()

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

OPclient = openai.OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)



@shared_task
def automate_post(country, account):
    """
    This function has been disabled as the news feature is no longer used.
    """
    try:
        description, hashtags = description_hashtags(account, "both")
        doc = telegram_channel_collection.find_one({"insta": account})
        
        # Instead of using news_data, we're returning an informational message
        message = "The news feature has been disabled as per user request."
        print(message)
        
        # Log the attempt to use disabled feature
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
    # Find the maximum existing _id and add 1 to it
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
    next_id = get_next_id(queue_collection)
    try:
        # Assuming the request body contains JSON data
        # body_unicode = request.data
        body_data = request

        # Log the received data
        logger.debug(f"Received body_data: {body_data}")

        image = request.POST.get('image_url')
        types = json.loads(request.POST.get('types', '[]'))
        accounts = json.loads(request.POST.get('accounts', '[]'))
        caption = request.POST.get('caption')
        time_gap = request.POST.get('time_gap')
        # cover = request.POST.get('cover')
        # print(cover, image)
        

        print(f"These are accounts: {accounts}")

        if not image:
            # Handle file upload case
            photo_file = request.FILES.get('photo')
            print(f"This is photo name: {photo_file}")
            if photo_file:
                filename = photo_file.name
                object_name = f"{filename.split('.')[0]}_{formatted_time}.{filename.split('.')[-1]}"
                temp_image_path = temp_dir + "/" + object_name
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
            cover = request.FILES.get('cover')  # Retrieve the uploaded file

            if cover:
                # Print uploaded file information for debugging
                print(f"This is cover name: {cover.name}")

                # Generate a unique filename with a timestamp
                filename = cover.name
                object_name = f"{filename.split('.')[0]}_{formatted_time}.{filename.split('.')[-1]}"
                temp_cover_path = f"{temp_dir}\\{object_name}"  # Ensure this is a valid string path

                # Save the uploaded file to a temporary location
                with open(temp_cover_path, 'wb') as temp_image:
                    for chunk in cover.chunks():
                        temp_image.write(chunk)

                # Upload the saved file to MinIO
                minio_client.fput_object(bucket_name, object_name, temp_cover_path)

            else:
                print("No cover file uploaded!")  # Print if no cover file is provided
                pass
            

        elif image:
            # Handle image URL case
            image_url = image
            print(f"this is image url: {image_url}")
            response = requests.get(image_url)
            if response.status_code == 200:
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                    
                # Sanitize the object name
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

        else:
            return JsonResponse({"error": "Bad request."}, status=400)

        # Prepare document for MongoDB insertion
        document = {
            "id": next_id,
            "username": username,
            "timestamp": formatted_time,
            "path": object_name,
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

        # Update status messages based on types
        for acc in document["accounts"]:
            if "story" in types:
                acc["story_status"] = None
                acc["story_message"] = "Not started."
            if "post" in types:
                acc["post_status"] = None
                acc["post_message"] = "Not started."

        # Insert into MongoDB
        try:
            result = queue_collection.insert_one(document)
            if not result.inserted_id:
                return JsonResponse({"error": "Failed to insert document in DB."}, status=500)
        except DuplicateKeyError:
            return JsonResponse({"error": "Duplicate path found in the database. Path must be unique."}, status=400)

        # Trigger celery task
        if 'reels' in types and temp_cover_path:
            queue.delay(time_gap, accounts, types, caption, temp_image_path, document["id"], temp_cover_path)
        elif 'reels' in types and not temp_cover_path:
            queue_notcover.delay(time_gap, accounts, types, caption, temp_image_path, document["id"])
        else:
            queue.delay(time_gap, accounts, types, caption, temp_image_path, document["id"])

        return JsonResponse({"message": "Task triggered successfully!"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format in request body."}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def pub(type, id, account, session, caption, image, cover):
    if type == "story":
        try:
            session.photo_upload_to_story(image)
            update_status("story", id, account, True, "", "")
            return
        except ClientConnectionError:
            update_status("story", id, account, False, "ClientConnectionError", "")
            raise Exception('ClientConnectionError')
        except Exception as e:
            update_status("story", id, account, False, str(e), "")
            raise Exception(str(e))

    if type == "post":
        try:
            session.set_proxy(PROXY_URL)
            session.photo_upload(image, caption)
            update_status("post", id, account, True, "", caption)
            return
        except ClientConnectionError:
            update_status("post", id, account, False, "ClientConnectionError", caption)
            raise Exception('ClientConnectionError')
        except Exception as e:
            update_status("post", id, account, False, str(e), caption)
            raise Exception(str(e))
        
    if type == "reels":
        try:
            
            session_record = instagram_session_collection.find_one({"username": account})
            # Deserialize the session JSON
            session_json = session_record.get("session_json")
            cl.set_proxy(PROXY_URL)
            cl.set_settings(session_json)
            if cover:
                cl.clip_upload(image, caption, cover)    
            else:
                cl.clip_upload(image, caption)
                update_status("reels", id, account, True, "", caption)
                return
        except ClientConnectionError:
            update_status("reels", id, account, False, "ClientConnectionError", caption)
            raise Exception('ClientConnectionError')
        except Exception as e:
            update_status("reels", id, account, False, str(e), caption)
            raise Exception(str(e))
        
def pub_reels_withoutcover(type, id, account, session, caption, image):
    if type == "story":
        try:
            session.photo_upload_to_story(image)
            update_status("story", id, account, True, "", "")
            return
        except ClientConnectionError:
            update_status("story", id, account, False, "ClientConnectionError", "")
            raise Exception('ClientConnectionError')
        except Exception as e:
            update_status("story", id, account, False, str(e), "")
            raise Exception(str(e))

    if type == "post":
        try:
            session.set_proxy(PROXY_URL)
            session.photo_upload(image, caption)
            update_status("post", id, account, True, "", caption)
            return
        except ClientConnectionError:
            update_status("post", id, account, False, "ClientConnectionError", caption)
            raise Exception('ClientConnectionError')
        except Exception as e:
            update_status("post", id, account, False, str(e), caption)
            raise Exception(str(e))
        
    if type == "reels":
        try:
            
            session_record = instagram_session_collection.find_one({"username": account})
            # Deserialize the session JSON
            session_json = session_record.get("session_json")
            cl.set_proxy(PROXY_URL)
            cl.set_settings(session_json)
            cl.get_timeline_feed()
            cl.clip_upload(image, caption)
            update_status("reels", id, account, True, "", caption)
            return
        except ClientConnectionError:
            update_status("reels", id, account, False, "ClientConnectionError", caption)
            raise Exception('ClientConnectionError')
        except Exception as e:
            update_status("reels", id, account, False, str(e), caption)
            raise Exception(str(e))



@shared_task(bind=True)
def queue(self, gap, accounts, types, caption, image, id, cover, null="null"):
    print(f"Arguments received: {gap}, {accounts}, {types}, {caption}, {image}, {id}, {cover}")
    gap_int = int(gap)
    gap = gap_int * 60
    for account in accounts:
        for username, session in insta:
            if username == account:
                if "story" in types:
                    try:
                        pub("story", id, account, session, caption, image)
                    except Exception:
                        print('handled')
                        continue
                if "post" in types:
                    try:
                        if "aicaption" in types:
                            description, hashtags = description_hashtags(username, "both")
                            private_caption = get_caption(account, caption, hashtags, description, id)
                            pub("post", id, account, session, private_caption, image)
                        else:
                            pub("post", id, account, session, caption, image)
                    except Exception as e:
                        print(str(e))
                        continue
                if "reels" in types:
                    try:
                        if "aicaption" in types:
                            description, hashtags = description_hashtags(username, "both")
                            private_caption = get_caption(account, caption, hashtags, description, id)
                            pub("reels", id, account, session, private_caption, image, cover)
                        else:
                            pub("reels", id, account, session, caption, image, cover)
                    except Exception as e:
                        print(str(e))
                        continue
        sleep(gap)
    os.remove(image)
    trigger_status(id, False)
    
@shared_task(bind=True)
def queue_notcover(self, gap, accounts, types, caption, image, id, null="null"):
    print(f"Arguments received: {gap}, {accounts}, {types}, {caption}, {image}, {id}")
    gap_int = int(gap)
    gap = gap_int * 60
    for account in accounts:
        for username, session in insta:
            if username == account:
                if "story" in types:
                    try:
                        pub("story", id, account, session, caption, image)
                    except Exception:
                        print('handled')
                        continue
                if "post" in types:
                    try:
                        if "aicaption" in types:
                            description, hashtags = description_hashtags(username, "both")
                            private_caption = get_caption(account, caption, hashtags, description, id)
                            pub("post", id, account, session, private_caption, image)
                        else:
                            pub("post", id, account, session, caption, image)
                    except Exception as e:
                        print(str(e))
                        continue
                if "reels" in types:
                    try:
                        if "aicaption" in types:
                            description, hashtags = description_hashtags(username, "both")
                            private_caption = get_caption(account, caption, hashtags, description, id)
                            pub_reels_withoutcover("reels", id, account, session, private_caption, image)
                        else:
                            pub_reels_withoutcover("reels", id, account, session, caption, image)
                    except Exception as e:
                        print(str(e))
                        continue
        sleep(gap)
    os.remove(image)
    trigger_status(id, False)


def update_status(type, document_id, account_name, status, e, caption):
    global index
    global message
    rec_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if type == "story":
        index = "story_status"
        message = "story_message"
    elif type == "post":
        index = "post_status"
        message = "post_message"
    elif type == "reels":
        index = "post_status"
        message = "post_message"

    document_id = int(document_id)
    if status:
        document = queue_collection.find_one({"id": document_id})
        if document:
            try:
                if type == "post":
                    queue_collection.update_one(
                        {"id": document_id, "accounts.username": account_name},
                        {
                            "$set": {
                                f"accounts.$.{index}": status,
                                f"accounts.$.{message}": "Published!",
                                "accounts.$.lastCheck": rec_time,
                                "accounts.$.caption": caption
                            }
                        }
                    )
                else:
                    queue_collection.update_one(
                        {"id": document_id, "accounts.username": account_name},
                        {
                            "$set": {
                                f"accounts.$.{index}": status,
                                f"accounts.$.{message}": e,  # ✅ Set to actual error message
                                "accounts.$.lastCheck": rec_time
                            }
                        }
                    )

            except Exception as err:
                print(str(err))

    if status == False:
        document = queue_collection.find_one({"id": document_id})
        if document:
            if type == "post":
                queue_collection.update_one(
                    {"id": document_id, "accounts.username": account_name},
                    {
                        "$set": {
                            f"accounts.$.{index}": status,
                            f"accounts.$.{message}": e,
                            "accounts.$.lastCheck": rec_time,
                            "accounts.$.caption": caption
                        }
                    }
                )
            else:
                queue_collection.update_one(
                    {"id": document_id, "accounts.username": account_name},
                    {
                        "$set": {
                            f"accounts.$.{index}": status,
                            f"accounts.$.{message}": "Published!",
                            "accounts.$.lastCheck": rec_time
                        }
                    }
                )
    if status == None:
        document = queue_collection.find_one({"id": document_id})
        if document:
            if type == "post":
                queue_collection.update_one(
                    {"id": document_id, "accounts.username": account_name},
                    {
                        "$set": {
                            f"accounts.$.{index}": status,
                            f"accounts.$.{message}": e,
                            "accounts.$.lastCheck": rec_time,
                            "accounts.$.caption": caption
                        }
                    }
                )
            else:
                queue_collection.update_one(
                    {"id": document_id, "accounts.username": account_name},
                    {
                        "$set": {
                            f"accounts.$.{index}": status,
                            f"accounts.$.{message}": e,
                            "accounts.$.lastCheck": rec_time
                        }
                    }
                )


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
            types = doc.get("types")
            post_check = False
            story_check = False
            if "post" in types:
                post_check = True
            if "story" in types:
                story_check = True
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
            if false_count > 0:
                Err = True
            else:
                Err = False
            if post_check == True and story_check == True:
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
                "true_percentage": int((true_count / (total_count * odd)) * 100)
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
            post_message = account.get('post_message')  # New
            story_message = account.get('story_message')  # New
            active = account.get('active')  # New

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
            account['post_message'] = post_message  # New
            account['story_message'] = story_message  # New

        Err = false_count > 0
        total_count = len(doc.get('accounts', []))
        j2 = {
            "id": id,
            "image": image,
            "timestamp": timestamp,
            "account_count": total_count,
            "caption": caption,
            "Error": Err,
            "true_percentage": int((true_count / (total_count * 2)) * 100),
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
    gap = doc.get('time_gap')
    image = doc.get('path')
    caption = doc.get('caption')

    temp_dir = '/tmp'
    image_url = f"http://{SERVER}/image/" + image

    # Download the image from the URL into a temporary file
    response = requests.get(image_url)
    if response.status_code == 200:
        # Create a temporary directory
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Create a temporary file to store the image data
        temp_image_path = os.path.join(temp_dir, 'temp_image.jpg')
        with open(temp_image_path, 'wb') as temp_image:
            temp_image.write(response.content)
    else:
        # Handle the case when image download fails
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

            if len(account_issues) > 1:  # Ensure that there are issues to report
                arr.append(account_issues)

    queue_retry.delay(arr, id, temp_image_path, gap, caption)
    return JsonResponse({"message": "Task triggered successfully!"})

    # queue.delay(time_gap, accounts, types, caption, temp_image_path, id)


@shared_task(
    bind=True)
def queue_retry(self, status_arr, id, image, gap, caption):
    gap = int(gap) * 60
    for account in status_arr:
        account_len = int(len(account))
        for username, session in insta:
            if username == account[0]:
                for i in range(1, account_len):
                    if account[i] == "story":
                        try:
                            update_status("story", id, account[0], None, "retrying!")
                            pub("story", id, account[0], session, caption, image)
                        except Exception:
                            print('handled')
                            continue
                    if account[i] == "post":
                        try:
                            update_status("post", id, account[0], None, "retrying!")
                            pub("post", id, account[0], session, caption, image)
                        except Exception:
                            print('handled')
                            continue
        sleep(gap)
    os.remove(image)
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
        {
            "$set": {
                "active": status
            }
        }
    )


def description_hashtags(username, mode):
    document = instagram_session_collection.find_one({"username": username})
    if mode == "description":
        description = document.get("description")
        return description
    if mode == "hashtags":
        hashtags = document.get("hashtags")
        return hashtags
    else:
        hashtags = document.get("hashtags")
        description = document.get("description")
        return description, hashtags


def run_gpt(account_name, caption, description, hashtags, queue_id):
    # id of the master prompt- change it to dynamic after demo
    try:
        id = 100
        master_prompt = prompt_collection.find_one({"id": id})
        master_prompt = master_prompt.get('prompt')
        # Format the system message with values from the JSON file
        system_message = master_prompt.format(
            Account_Name=account_name,
            ACCOUNT_SUMMARY=description,
            RELATED_HASHTAGS=hashtags
        )
        caption = f"""Write a caption for a post of my personal Instagram page. 
        This particular post contains a picture with the following keywords:{caption}. 
        Add 15 Hashtags and no more. The first 11 Hashtags of the 15 should be low competitive. 
        The first 4 of this 15 should be related to the keywords and low competitive. 
        After this you add 4 medium competitive Hashtags and 2 high competitive Hashtags. 
        Do not tell which hashtags are what, just add them, so I can copy it perfectly for Instagram. 
        Do not include anything but the caption.
        Write the Caption in English and use a friendly "you" form. 
        The reel should go viral. \nie. 
        CAPTION: [write caption here]"""
        completion = OPclient.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": caption}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        update_status("post", queue_id, account_name, False, str(e), "")
        raise Exception('Err')

def run_gpt_news(account_name, caption, description, hashtags, queue_id):
    """
    Modified news caption generator that works without the news feature.
    Uses standard caption generation instead.
    """
    return run_gpt(account_name, caption, description, hashtags, queue_id)

def get_caption(account_name, caption, description, hashtags, queue_id):
    caption = run_gpt(account_name, caption, description, hashtags, queue_id)
    caption = caption.replace("Caption:", "").replace("CAPTION:", "").replace('"', "").strip()
    return caption
def get_caption_news(account_name, caption, description, hashtags, queue_id):
    """
    Modified function that falls back to standard caption generation
    """
    return get_caption(account_name, caption, description, hashtags, queue_id)
