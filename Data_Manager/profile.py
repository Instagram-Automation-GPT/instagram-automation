import os
import json
import logging
from datetime import datetime
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.urls import reverse
import tempfile
from instagrapi.exceptions import ClientConnectionError, ChallengeRequired
from urllib3.exceptions import ResponseError
from io import BytesIO
import requests
from . import instagram_session, mongo_session, minio_session
from minio.error import S3Error
from io import BytesIO
import hashlib
from instagrapi import Client
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

cl = Client()

# Initialize logger
logger = logging.getLogger(__name__)

# MongoDB collections
db = mongo_session.get_mongo_session()
collection = db["Published"]
queue_collection = db["Queue"]
queue_error_collection = db["Queue_Errors"]
instagram_session_collection = db["instagram_session"]
telegram_channel_collection = db["telegram_channels"]

# MinIO configuration
bucket_name = 'josef'
minio_client = minio_session.get_minio_session()

# Instagram clients
insta = instagram_session.get_insta_clients()
logger.info(f"Loaded Instagram sessions: {insta}")

# Temporary directory
temp_dir = '/tmp'

@login_required
@api_view(['POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def profile_change(request):
    """Handles profile picture change for a single Instagram account."""
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H%M%S")

    try:
        # Get the username and image from the request
        username = request.POST.get('username')
        image = request.FILES.get('image')

        if not username:
            return JsonResponse({"error": "No username provided!"}, status=400)

        if not image:
            return JsonResponse({"error": "No file uploaded!"}, status=400)

        # Save the uploaded image to MinIO
        filename = image.name
        object_name = f"{os.path.splitext(filename)[0]}_{formatted_time}{os.path.splitext(filename)[1]}"

        try:
            minio_client.put_object(
                bucket_name,
                object_name,
                image.file,
                length=image.size,
                content_type=image.content_type,
            )
            logger.info(f"Image uploaded to MinIO: {object_name}")
        except ResponseError as error:
            logger.error(f"Failed to save image in MinIO: {error}")
            return JsonResponse({"error": "Failed to save image in MinIO!"}, status=500)

        # Construct a Django-served URL for the uploaded image
        static_url = f"http://{request.get_host()}{reverse('profile_image', args=[object_name])}"
        logger.info(f"Static URL for the image: {static_url}")

        # Fetch the Instagram session for the given username
        session_record = instagram_session_collection.find_one({"username": username})
        if not session_record:
            return JsonResponse({"error": f"No session found for username: {username}"}, status=404)

        # Deserialize the session JSON
        session_json = session_record.get("session_json")
        if not session_json:
            return JsonResponse({"error": "Session data is missing from the database."}, status=500)

        # Now fetch the image using requests (download it) to pass as a local file
        response = requests.get(static_url)
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to download image from MinIO."}, status=500)

        # Create a temporary file to store the image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
            logger.info(f"Temporary file saved at: {tmp_file_path}")

        # Use the temporary file in the Instagram API
        try:
            cl.set_proxy(PROXY_URL)
            cl.set_settings(session_json)
            cl.get_timeline_feed()
            cl.account_change_picture(tmp_file_path)
            logger.info(f"Profile picture changed for {username}")
            return JsonResponse({"success": f"Profile picture updated for {username}."})
        except (ClientConnectionError, ChallengeRequired, ValueError) as e:
            logger.error(f"Error changing profile picture for {username}: {e}")
            return JsonResponse({"error": f"Failed to update profile picture for {username}: {e}"}, status=500)

    except Exception as e:
        logger.exception("An error occurred during profile change:")
        return JsonResponse({"error": str(e)}, status=500)
    
    
def serve_profile_image(request, image_name):
    """Serve the image from MinIO using a Django view."""
    try:
        response = minio_client.get_object(bucket_name, image_name)
        return HttpResponse(response, content_type="image/jpeg")
    except Exception as e:
        logger.error(f"Failed to retrieve image: {e}")
        return JsonResponse({"error": "Image not found!"}, status=404)
    
bucket_name_profile = "profile"

def serve_user_profile_image(request, user_profile_image):
    """Serve the image from MinIO using a Django view."""
    try:
        # Possible extensions for the image
        possible_extensions = ['.jpg', '.jpeg', '.png']

        # Try to find the image with one of the possible extensions
        for ext in possible_extensions:
            image_name = f"{user_profile_image}{ext}"
            try:
                # Try to fetch the image from MinIO
                response = minio_client.get_object(bucket_name_profile, image_name)

                # If image is found, return the image as an HttpResponse
                return HttpResponse(response, content_type="image/jpeg")
            except Exception as e:
                # If image with this extension doesn't exist, move to the next extension
                continue
        
        # If no image was found for any extension, return an error
        return JsonResponse({"error": "Image not found!"}, status=404)
    
    except Exception as e:
        logger.error(f"Failed to retrieve image: {e}")
        return JsonResponse({"error": "Image not found!"}, status=404)
    

def ensure_bucket_exists():
    """Check if the MinIO bucket exists and create it if not."""
    try:
        if not minio_client.bucket_exists(bucket_name_profile):
            minio_client.make_bucket(bucket_name_profile)
            logger.info(f"Bucket '{bucket_name_profile}' created successfully.")
    except S3Error as e:
        logger.exception("Error checking/creating MinIO bucket")
        raise e
@csrf_exempt
def get_profile_picture(request):
    try:
        # Get parameters
        username = request.POST.get('username')
        refetch = request.POST.get('refetch', 'false').lower() == 'true'

        if not username:
            return JsonResponse({"error": "No username provided!"}, status=400)

        # Ensure MinIO bucket exists
        ensure_bucket_exists()

        # Check if image already exists in MongoDB
        existing_record = instagram_session_collection.find_one({"username": username})
        # image_path = f"{bucket_name_profile}/{username}.jpg"

        if existing_record and not refetch:
            # Construct the URL using the MinIO client
            static_url = f"http://{request.get_host()}{reverse('user_profile_image', args=[username])}"
            return JsonResponse({"profile_picture_url": static_url})

        # Retrieve session from MongoDB
        session_record = instagram_session_collection.find_one({"username": username})
        if not session_record:
            return JsonResponse({"error": f"No session found for username: {username}"}, status=404)

        session_json = session_record.get("session_json")
        if not session_json:
            return JsonResponse({"error": "Session data is missing from the database."}, status=500)

        # Initialize Instagram client with session
        cl = Client()
        cl.set_settings(session_json)

        # Fetch user info
        user_info = cl.user_info_by_username(username)
        profile_pic_url = user_info.profile_pic_url_hd

        # Fetch image from URL
        response = requests.get(profile_pic_url)
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to download profile picture"}, status=500)

        image_data = response.content

        # Generate a hash to check if the image has changed
        new_image_hash = hashlib.md5(image_data).hexdigest()
        old_image_hash = existing_record.get("image_hash") if existing_record else None

        if old_image_hash == new_image_hash and not refetch:
            # Construct the URL using the MinIO client
            static_url = f"http://{request.get_host()}{reverse('user_profile_image', args=[username])}"
            return JsonResponse({"profile_picture_url": static_url})
        
        static_url = f"http://{request.get_host()}{reverse('user_profile_image', args=[username])}"
        # Save image to MinIO
        minio_client.put_object(
            bucket_name_profile,
            f"{username}.jpg",
            BytesIO(image_data),
            length=len(image_data),
            content_type="image/jpeg",
        )

        # Update database with new image info
        instagram_session_collection.update_one(
            {"username": username},
            {"$set": {
                "image_url": static_url,
                "image_hash": new_image_hash
            }},
            upsert=True
        )

        # Construct the URL using the MinIO client
        static_url = f"http://{request.get_host()}{reverse('user_profile_image', args=[username])}"
        return JsonResponse({"profile_picture_url": static_url})

    except S3Error as e:
        logger.exception("MinIO Error")
        return JsonResponse({"error": f"MinIO Error: {str(e)}"}, status=500)

    except Exception as e:
        logger.exception("An error occurred while fetching profile picture.")
        return JsonResponse({"error": str(e)}, status=500)