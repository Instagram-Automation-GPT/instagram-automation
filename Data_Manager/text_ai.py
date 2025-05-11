import openai
import json
import os
from . import mongo_session
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import random
import requests
from datetime import datetime, timedelta

db = mongo_session.get_mongo_session()
prompt_collection = db["master_prompt"]

client = openai.OpenAI(
    api_key="YOUROPENAIAPIKEY"
)


def get_caption(account_name, caption, description, hashtags):
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

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": caption}
            ]
        )
        return completion.choices[0].message.content
    except:
        raise Exception('Err')


@csrf_exempt
def image_command(request):
    """Generate a general topic summary for content"""
    body = json.loads(request.body)
    general = body.get('general')
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user",
             "content": f"Given the input text '{general}', identify a general topic that summarizes the main subject in just 2 words."}
        ]
    )
    return JsonResponse({'message': completion.choices[0].message.content}, status=200)


@csrf_exempt
def title_command(request):
    """Generate a new title for content creation"""
    body = json.loads(request.body)
    general = body.get('general')
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user",
             "content": f"Given the input text '{general}', generate a new catchy title for creating a poster, maximum 6 words."}
        ]
    )
    return JsonResponse({'message': completion.choices[0].message.content}, status=200)


# The following functions related to news processing have been disabled
# as per user request to remove news feature

def read_json_file(country):
    """Disabled news feature"""
    return None


def news_data(country):
    """Disabled news feature"""
    raise Exception("News feature has been disabled")


def check_duplicate(number, country):
    """Disabled news feature"""
    return False


def submit_id(number, country):
    """Disabled news feature"""
    pass
