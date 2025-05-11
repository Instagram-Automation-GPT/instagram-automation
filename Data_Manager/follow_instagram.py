from instagrapi import Client
import json
from .mongo_session import get_mongo_session
import instagrapi
from .instagram_session import challenge_code_handler
from django.http import JsonResponse
import time
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import os
import tempfile
from bson.json_util import dumps
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

db = get_mongo_session()
collection = db["session_extractor"]

# Initialize instagrapi client
client = Client()
client.set_proxy(PROXY_URL)

def ensure_collection_exists(db, collection_name):
    # Check if the collection exists
    if collection_name not in db.list_collection_names():
        # Create the collection if it doesn't exist
        db.create_collection(collection_name)
        print(f"Collection '{collection_name}' created.")
    else:
        print(f"Collection '{collection_name}' already exists.")

@csrf_exempt
def follow_instagram_login(request):
    ensure_collection_exists(db, 'session_extractor')

    if request.method == 'POST':
        try:            
            data = json.loads(request.body)
            insta_user = data.get('username')
            insta_password = data.get('password')
            insta_code = data.get('code')
            
            if not insta_user or not insta_password:
                return JsonResponse({'message': "Username and password are required."}, status=400)            
            
            code_data = {'email_code': insta_code}
            user = request.user.username
            current_time = datetime.now()
            register_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            if code_data:
                # Write code to a temporary JSON file
                with open('email_code.json', 'w') as json_file:
                    json.dump(code_data, json_file)
        
            try:  
                login_extractors(insta_user, insta_password, user, register_time)
                return JsonResponse({'message': f"{insta_user} user registered successfully."}, status=200)
            except Exception as e:
                return JsonResponse({'message': f"Error while registering account: {str(e)}"}, status=500)
        except Exception as e:
            # Log the exception for debugging purposes
            print(f"Error while registering account: {str(e)}")
            # Return error response
            return JsonResponse({'message': f"Error while registering account: {str(e)}"}, status=500)
    else:
        return JsonResponse({'message': "Invalid request method. Only POST is allowed."}, status=405)


# Function to save session
def save_session(client, username, password, user, register_time):
    session_json = client
    session_data = {
        "username": username,
        "session_json": session_json,
        "user": user,
        "timestamp": register_time,
        "password": password
    }
    collection.insert_one(session_data)

def login_extractors(username, password, user, register_time):
    # Check if a saved session exists
    collection = db["session_extractor"]
    session_data = collection.find_one(sort=[("timestamp", -1)])  # Get the latest session
    
    if session_data:
        client.load_settings(json.loads(session_data["session_json"]))
        print("Logged in using saved session")
    else:
        # If no session found, login
        client.challenge_code_handler = challenge_code_handler
        
        client.set_proxy(PROXY_URL)
        client.login(username, password)
        
        # Save settings to a temporary path
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_path = temp_file.name
            client.dump_settings(temp_path)

        # Read the saved JSON content
        with open(temp_path, 'r') as file:
            json_content = json.load(file)

        # Remove the temporary file
        os.unlink(temp_path)
        
        # Save session for future use
        save_session(json_content, username, password, user, register_time)
        print("Logged in and session saved")
        
    return True

# Function to get user ID from username
def user_id_from_username(username: str):
    
    db = get_mongo_session()
    collection = db["session_extractor"]
    session_data = collection.find_one(sort=[("timestamp", -1)])  # Get the latest session
    print(f"This is the username: {username}")
    if session_data:
        client = Client()
        client.set_proxy(PROXY_URL)
        client.session_data = session_data["session_json"]
        print(client.session_data)
        client.set_settings(client.session_data)
        print("Logged in using saved session")
        
    user = client.user_info_by_username(username)
    return user.pk

# Function to follow a user by username
def follow_user(username: str):
    user_id = user_id_from_username(username)
    client.user_follow(user_id)
    print(f"Followed user '{username}' successfully!")

@csrf_exempt
def getting_user_id(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            target_username = data.get('targetusername')
            follow_number = data.get('number')
            follow_category = data.get('category')
            print(target_username)
            client = load_insta_session()
            
            userName = user_id_from_username(target_username)
            print(f"This is user id: {userName}")
            getting_user_followers(userName, target_username, follow_number, follow_category)
            
            return JsonResponse({'message': f"target username: {target_username}"}, status=200)
        except Exception as e:
            return JsonResponse({'message': f"Error while registering account: {str(e)}"}, status=500)

def load_insta_session():
    # Retrieve the session from MongoDB and load it into the client
    db = get_mongo_session()
    collection = db["session_extractor"]
    session_data = collection.find_one(sort=[("timestamp", -1)])  # Get the latest session
    
    if session_data:
        client = Client()
        client.set_proxy(PROXY_URL)
        client.session_data = session_data["session_json"]
        print(client.session_data)
        client.set_settings(client.session_data)
        print("Logged in using saved session")
        
        return client
    else:
        return JsonResponse({'message': "No saved extractor account found."}, status=500)

def getting_user_followers(user_id, target_username, follow_number, follow_category):
    
    db = get_mongo_session()
    collection = db["session_extractor"]
    session_data = collection.find_one(sort=[("timestamp", -1)])  # Get the latest session
    
    if session_data:
        client = Client()
        client.set_proxy("socks5://3fYoKEvjbU9rThAd:1A4hN3LROvI04dbW@geo.iproyal.com:32325")
        client.session_data = session_data["session_json"]
        print(client.session_data)
        client.set_settings(client.session_data)
        print("Logged in using saved session")
        print("Getting folowers...")
    
    followers, _ = client.user_followers_gql_chunk(user_id, follow_number)  # Unpack the tuple
    followers_list = []
    follow_number = int(follow_number)
    for follower_info in followers:
        followers_list.append({
            'user_id': follower_info.pk,
            'username': follower_info.username,
            'full_name': follower_info.full_name,
            'profile_pic_url': str(follower_info.profile_pic_url),  # Ensure URL is a string
            'target_username': target_username,
            'follow_category': follow_category
        })
    
    # Save followers to MongoDB
    db = get_mongo_session()
    ensure_collection_exists(db, "instagram_followers")
    
    collection = db["instagram_followers"]
    for follower in followers_list:
        follower['_id'] = follower['user_id']
        collection.update_one({'_id': follower['user_id']}, {'$set': follower}, upsert=True)
    # print(f"Saved {len(followers_list)} followers to MongoDB in collection '{followers}'")

# Function to get instagram followers

def showing_instagram_followers(request):
    if request.method == 'GET':
        try:
            db = get_mongo_session()
            collection = db["instagram_followers"]

            # Retrieve all followers data
            followers = list(collection.find({}, {'_id': 0}))  # Exclude MongoDB ID from the result

            return JsonResponse({'followers': followers}, status=200, safe=False)
        except Exception as e:
            return JsonResponse({'message': f"Error while fetching followers: {str(e)}"}, status=500)
    else:
        return JsonResponse({'message': "Invalid request method. Only GET is allowed."}, status=405)

def showing_instagram_extractors_account(request):
    if request.method == 'GET':
        try:
            # Connect to MongoDB
            db = get_mongo_session()
            collection = db["session_extractor"]

            # Retrieve the latest session data
            session_data = collection.find_one(sort=[("timestamp", -1)])  # Get the latest session

            if session_data:
                # Extract only the username and password fields
                result = {
                    'username': session_data.get('username', 'N/A'),
                    'password': session_data.get('password', 'N/A')
                }
                return JsonResponse(result, status=200)
            else:
                return JsonResponse({'message': 'No saved session found.'}, status=404)

        except Exception as e:
            return JsonResponse({'message': f"Error: {str(e)}"}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method.'}, status=405)