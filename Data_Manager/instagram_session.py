import time
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from instagrapi import Client
from instagrapi.types import StoryMention, StoryMedia, StoryLink, StoryHashtag
from .mongo_session import get_mongo_session
import tempfile
import json
import os
from datetime import datetime
from celery import shared_task
from instagrapi.mixins.challenge import ChallengeChoice, ChallengeRequired
from django.shortcuts import render
from django.shortcuts import redirect
import pdb
import logging
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.decorators import api_view, parser_classes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger()

# Get proxy configuration from environment variables
PROXY_USERNAME = os.getenv('PROXY_USERNAME')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD')
PROXY_HOST = os.getenv('PROXY_HOST')
PROXY_PORT = os.getenv('PROXY_PORT')

# Construct proxy URL
PROXY_URL = f"socks5://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"

# Get the MongoDB connection
db = get_mongo_session()
collection = db["instagram_session"]
collection.create_index([("username", 1)], unique=True)

insta_clients = []


# Function to get Instagram sessions from the collection
def get_insta_session():
    # insta_clients.clear()
    existing_sessions = collection.find({"status": "Healthy"})
    for session in existing_sessions:
        print("sessiondata")
        print(session["session_json"])
        insta = Client()
        insta.session_data = session["session_json"]
        insta.set_settings(insta.session_data)
        username = session.get("username")
        insta_clients.append([username, insta])
    return insta_clients


get_insta_session()


# Function to return Instagram clients
def get_insta_clients():
    return insta_clients


def load_insta_session(username):
    # Check if there is an entry for the username in the collection
    existing_session = collection.find_one({"username": username})
    if existing_session:
        # If session exists, load it and return
        insta = Client()
        insta.session_data = existing_session["session_json"]
        print("session data")
        print(insta.session_data)
        insta.set_settings(insta.session_data)
        return insta
    else:
        return False


def save_insta_session(insta, username, user, register_time, description, hashtags, password, status, msg):
    # Save instagram session data and associated instagram account id
    session_json = insta
    session_data = {
        "username": username,
        "session_json": session_json,
        "user": user,
        "timestamp": register_time,
        "antiBan": False,
        "status": status,
        "description": description,
        "hashtags": hashtags,
        "password": password,
        "error": msg
    }
    collection.insert_one(session_data)


def update_insta_session(username, status, msg):
    update_result = collection.update_one(
        {"username": username},
        {
            "$set": {
                "status": status,
                "error": msg
            }
        }
    )
    return update_result.modified_count


def challenge_code_handler(username, choice):
    if choice == ChallengeChoice.EMAIL:
        # Check if the file exists
        email_code_file = os.path.normpath('email_code.json')
        if os.path.exists(email_code_file):
            # Read the email code from the JSON file
            with open(email_code_file, 'r') as json_file:
                data = json.load(json_file)
                insta_code = data.get('email_code', '')

            try:
                if os.path.exists(email_code_file):
                    os.remove(email_code_file)
            except Exception as e:
                print(f"Error removing email code file: {str(e)}")

            # Check if the insta_code contains digits
            if insta_code.isdigit():
                # Format the code as needed
                formatted_code = insta_code  # Add your formatting logic here if needed
                return formatted_code
        else:
            # If the file does not exist, handle accordingly
            return True

    elif choice == ChallengeChoice.SMS:  # Assuming you meant SMS here
        return True

    return False


@login_required
def register(request):
    if request.method == 'POST':
        try:
            insta_user = request.POST.get('username')
            insta_password = request.POST.get('password')
            insta_code = request.POST.get('code')
            twostep = request.POST.get('twostep')
            description = request.POST.get('description')
            hashtags = request.POST.get('hashtags')

            user = request.user.username
            current_time = datetime.now()
            register_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            insta = load_insta_session(insta_user)
            code_data = {'email_code': insta_code}

            # Write code to a temporary json file
            if code_data:
                # Create normalized path for the email code file
                email_code_file = os.path.normpath('email_code.json')
                
                # Write code to a temporary JSON file
                with open(email_code_file, 'w') as json_file:
                    json.dump(code_data, json_file)

            if not insta:
                try:
                    insta = Client()
                    insta.set_proxy(PROXY_URL)
                    insta.challenge_code_handler = challenge_code_handler
                    
                    if twostep: 
                        insta.login(insta_user, insta_password, verification_code=twostep)
                        
                    insta.login(insta_user, insta_password)

                    # Save settings to a temporary path
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                        temp_path = temp_file.name
                        insta.dump_settings(temp_path)

                    # Read the saved JSON content
                    with open(temp_path, 'r') as file:
                        json_content = json.load(file)

                    # Remove the temporary file
                    os.unlink(temp_path)

                    save_insta_session(json_content, insta_user, user, register_time, description, hashtags,
                                       insta_password, "Healthy", '')
                    get_insta_session()
                    return JsonResponse({'message': f"{insta_user} user registered successfully."}, status=200)
                except Exception as e:
                    return JsonResponse({'message': f"Error while registering account: {str(e)}"}, status=500)
            else:
                return JsonResponse({'message': f"User '{insta_user}' already exists."}, status=400)

        except Exception as e:
            # Log the exception for debugging purposes
            print(f"Error while registering account: {str(e)}")

            # Return error response
            return JsonResponse({'message': f"Error while registering account: {str(e)}"}, status=500)


    else:
        return JsonResponse({'message': 'Invalid request method'}, status=405)


@login_required
def sessions_list(request):
    # Check if there is an entry for the username in the collection
    existing_session = collection.find({})
    insta_clients = []
    if existing_session:
        for session in existing_session:
            # Exclude the _id field
            session.pop('_id', None)
            session.pop('session_json', None)
            insta_clients.append(session)
        return JsonResponse({'message': insta_clients}, status=200)
    else:
        return JsonResponse({'message': f"Error"}, status=400)


@login_required
def edit_session_list(request):
    # Updating hashtags and descprion of an account
    db = get_mongo_session()
    collection = db["instagram_session"]

    data = request.POST

    username = data.get('username')
    new_description = data.get('description')
    new_hashtags = data.get('hashtags')
    print(username, new_description, new_hashtags)

    update_data = {}

    if new_description:
        update_data["description"] = new_description

    if new_hashtags:
        update_data["hashtags"] = new_hashtags

    if not update_data:
        return JsonResponse({'error': 'No fields to update'}, status=400)

    result = collection.update_one(
        {"username": username},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return JsonResponse({'error': 'Account not found'}, status=404)

    return JsonResponse({'successfull': 'Account updated successfully'})


@login_required
@api_view(['POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def relogin(request):
    try:
        data = request
        user = data.POST.get('user')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON or missing user field'}, status=400)

    if not user:
        return JsonResponse({'error': 'User field is required'}, status=400)
    username = request.user.username
    document = collection.find_one({"username": user})

    if document:
        insta = Client()
        password = document.get('password')
        register_time = document.get('timestamp')
        description = document.get('description')
        hashtags = document.get('hashtags')

        try:
            insta.set_proxy(PROXY_URL)
            insta.login(user, password)
            # Save settings to a temporary path
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_path = temp_file.name
                insta.dump_settings(temp_path)

            # Read the saved JSON content
            with open(temp_path, 'r') as file:
                json_content = json.load(file)
                save_insta_session(json_content, user, username, register_time, description, hashtags, password,
                                   "Healthy", '')
                get_insta_session()
                return JsonResponse({'message': f"{user} user login successfully."}, status=200)
        except Exception as e:
            update_insta_session(username, "Unhealthy", str(e))
            return JsonResponse({'error': str(e)}, status=400)

@login_required
@api_view(['POST'])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def delete_session(request):
    try:
        data = request
        user = data.POST.get('user')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON or missing user field'}, status=400)

    if not user:
        return JsonResponse({'error': 'User field is required'}, status=400)
    username = request.user.username
    document = collection.find_one({"username": user})
    if document and document.get('user') == username:
        collection.delete_one({"username": user})
        return JsonResponse({'success': 'Session deleted successfully'}, status=200)
    else:
        return JsonResponse({'error': 'Unauthorized or session not found'}, status=403)
