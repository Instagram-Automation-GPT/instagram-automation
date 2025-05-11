import requests
import pymongo
from celery import shared_task


TOKEN = "Telegram Token"
chat_id = "Chat ID"
name = "Name"
message = "Happy Coding"
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"

@shared_task
def telegram_broadcast(TOKEN, chat_id, message, image_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(image_path, 'rb') as image_file:
        data = {
            'chat_id': chat_id,
            'caption': message
        }
        files = {
            'photo': image_file
        }
        response = requests.post(url, data=data, files=files)
        # Check if the request was successful (status code 200 means OK)
        if response.status_code == 200:
            return True
        else:
            return False