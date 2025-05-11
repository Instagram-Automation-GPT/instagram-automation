from instagrapi import Client
import json
from time import sleep
from celery import shared_task
from .mongo_session import get_mongo_session
import instagrapi
from .instagram_session import challenge_code_handler
from instagrapi.exceptions import ClientConnectionError, ChallengeRequired
from django.http import JsonResponse
import time
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from . import instagram_session
import os
import tempfile
from bson.json_util import dumps
import logging
from Django.celery import app
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

db = get_mongo_session()

insta = instagram_session.get_insta_clients()
print(insta)

# Get proxy configuration from environment variables
PROXY_USERNAME = os.getenv('PROXY_USERNAME')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD')
PROXY_HOST = os.getenv('PROXY_HOST')
PROXY_PORT = os.getenv('PROXY_PORT')

# Construct proxy URL
PROXY_URL = f"socks5://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"

@shared_task
def queue_follow(account, tofollows):
    for username, session in insta:
        if username == account:
            session.set_proxy(PROXY_URL)
            try:
                do_follow(account, session, tofollows)        
            except Exception as e:
                print(str(e))
                logger.error(f"Error in task for account {account}: {str(e)}")
    
def update_followed_by(account, followed_user_id):
    """
    Update the MongoDB collection by adding the account name to the 'followed_by' field
    for the user that was followed.
    
    Args:
    - account (str): The account performing the follow action.
    - followed_user_id (str): The ID of the user that was followed.
    """
    try:
        # Access the Instagram followers collection
        collection = db['instagram_followers']

        # Update the document by adding the account name to the followed_by array
        result = collection.update_one(
            {"user_id": followed_user_id},
            {"$addToSet": {"followed_by": account}}
        )

        if result.matched_count:
            logger.info(f"Updated 'followed_by' for user {followed_user_id} with account {account}")
        else:
            logger.warning(f"No matching document found for user_id {followed_user_id}. Could not update 'followed_by'.")

    except Exception as e:
        logger.error(f"Error updating 'followed_by' in MongoDB for user_id {followed_user_id}: {str(e)}")
        print(f"Error updating 'followed_by' in MongoDB for user_id {followed_user_id}: {str(e)}")
    
@app.task
def do_follow(account, session, tofollows):
    print(tofollows)
    for user_id in tofollows:
        session.user_follow(user_id)
        
        # Update the MongoDB collection for the followed user
        update_followed_by(account, user_id)
        
        print(f"Successfully followed {user_id} for account: {account}")
        logger.info(f"Successfully followed {user_id} for account: {account}")
        
        # Introduce a random delay between 1 to 2.5 minutes (60 to 150 seconds)
        delay = random.uniform(70, 250)
        print(f"Sleeping for {delay:.2f} seconds before the next follow...")
        time.sleep(delay)

# @login_required
@csrf_exempt
@api_view(['POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def follower_params(request):

    try:
        # Assuming the request body contains JSON data
        # body_unicode = request.data
        body_data = request

        # Log the received data
        logger.debug(f"Received body_data: {body_data}")
        
        target_accounts = json.loads(request.POST.get('accounts', '[]'))
        tofollows = json.loads(request.POST.get('accountstofollow', '[]'))

        print(f"These are targetted accounts: {target_accounts} and these are accounts to fllow: {tofollows}")

        # Trigger celery task
        for account in target_accounts:
            queue_follow.delay(account, tofollows)

        return JsonResponse({"message": "Task To follow triggered successfully!"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format in request body."}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
