import logging
from datetime import datetime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser
from instagrapi.exceptions import ClientConnectionError, ChallengeRequired
from . import instagram_session, mongo_session
from dotenv import load_dotenv
import os

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

# Initialize logger
logger = logging.getLogger(__name__)

# MongoDB collections
db = mongo_session.get_mongo_session()
instagram_session_collection = db["instagram_session"]

# Instagram clients
insta = instagram_session.get_insta_clients()
logger.info(f"Loaded Instagram sessions: {insta}")

@login_required
@api_view(['POST'])
@parser_classes([JSONParser])
def username_change(request):
    """Handles username change for a single Instagram account and updates MongoDB."""
    try:
        # Get the old and new username from the request
        old_username = request.data.get('old_username')
        new_username = request.data.get('new_username')
        
        session_record = instagram_session_collection.find_one({"username": old_username})
        if not session_record:
            return JsonResponse({"error": f"No session found for username: {old_username}"}, status=404)

        # Deserialize the session JSON
        session_json = session_record.get("session_json")
        if not session_json:
            return JsonResponse({"error": "Session data is missing from the database."}, status=500)

        # Attempt to change the username
        try:
            cl.set_proxy(PROXY_URL)
            cl.set_settings(session_json)
            cl.get_timeline_feed()
            cl.account_edit(username=new_username)
            logger.info(f"Username changed from {old_username} to {new_username}")

            # Update MongoDB record
            result = instagram_session_collection.update_one(
                {"username": old_username},
                {"$set": {"username": new_username}}
            )

            if result.modified_count == 0:
                logger.warning(f"No document found for {old_username}, or username is already updated.")

            return JsonResponse({"success": f"Username updated from {old_username} to {new_username}."})
        except (ClientConnectionError, ChallengeRequired, ValueError) as e:
            logger.error(f"Error changing username for {old_username}: {e}")
            return JsonResponse({"error": f"Failed to update username for {old_username}: {e}"}, status=500)

    except Exception as e:
        logger.exception("An error occurred during username change:")
        return JsonResponse({"error": str(e)}, status=500)
