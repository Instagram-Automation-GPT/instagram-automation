from celery import shared_task
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
from Data_Manager import mongo_session
import requests
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from dateutil import parser
from Data_Manager.publish import automate_post
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db = mongo_session.get_mongo_session()
collection = db["tasks"]

json_dir = "News"


@shared_task
def update_json():
    country = "en"
    today_date = datetime.today()
    formatted_date = today_date.strftime('%Y-%m-%d')
    url = f"https://api.worldnewsapi.com/top-news?source-country={country}&language=en&date={formatted_date}"
    api_key = os.getenv('WORLD_NEWS_API_KEY')

    headers = {
        'x-api-key': api_key
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        with open(f'{json_dir}/{country}-{formatted_date}.json', 'w') as f:
            json.dump(response.json(), f, indent=4)
        return True
    else:
        return f"Error: {response.status_code}"


@shared_task
def auto_posting():
    iran_tz = pytz.timezone('Asia/Tehran')
    now = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(iran_tz)
    print(now)
    five_minutes_from_now = now + timedelta(minutes=2)
    five_minutes_ago = now - timedelta(minutes=2)

    # Fetch all tasks
    all_tasks = list(collection.find())

    # Filter tasks within the desired time range
    tasks_to_execute = []
    for task in all_tasks:
        execution_time_str = task['execution_time']
        date_format = '%Y-%m-%d %H:%M:%S%z'

        date_obj = datetime.strptime(str(execution_time_str), date_format)
        print(date_obj)
        print(five_minutes_from_now)
        print(five_minutes_ago)
        if five_minutes_ago <= date_obj <= five_minutes_from_now and task.get('count') < task.get('news_count'):
            print("task")
            tasks_to_execute.append(task)
    print(tasks_to_execute)
    # Process each fetched task
    for task in tasks_to_execute:
        execution_time_str = task.get('execution_time')
        execution_time = parser.isoparse(execution_time_str).astimezone(iran_tz)
        gap = task.get('gap')
        count = task.get('count')
        country = task.get('country')
        user = task.get('user')

        # Calculate the time difference between now and the execution time
        time_difference = now - execution_time
        random_minute = random.randint(2, 10)
        next = now + timedelta(minutes=int(gap)) + timedelta(minutes=random_minute)
        next_time = next.replace(microsecond=0)
        next_time = str(next_time.astimezone(iran_tz))
        # Update the document to set 'started' to true
        collection.update_one(
            {'_id': task['_id']},
            {'$set': {'started': True,'execution_time': next_time,'count': count + 1}}
        )
        try:
            automate_post.delay(country,user)
        except Exception as e:
            print(str(e))


@csrf_exempt
def save_schedule(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            required_fields = ['country', 'user', 'gap', 'news_count', 'execution_time']
            if not all(field in data for field in required_fields):
                return JsonResponse({'error': 'Missing fields in request body'}, status=400)
            data['started'] = False
            data['count'] = 0
            collection.insert_one(data)
            return JsonResponse({'message': 'Data saved successfully'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

