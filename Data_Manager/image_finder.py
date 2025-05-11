import json
import os
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import random
from . import instagram_session
from django.contrib.auth.decorators import login_required
import requests
key = "TOKEN TO GET IMAGES FROM PIXABAY"


@login_required
def get_image(request, keyword):
    try:
        # Assuming the request body contains JSON data
        base_url = "https://pixabay.com/api/?key="
        image_url = base_url + key + "&q=" + keyword + "&image_type=photo"
        # Download the image from the URL into a temporary file
        response = requests.get(image_url)
        if response.status_code == 200:
            # Assuming the response is in JSON format
            data = response.json()
            # Extracting image URLs from the response
            image_urls = [hit['webformatURL'] for hit in data['hits']]
            if len(image_urls) > 8:
                image_urls = random.sample(image_urls, 8)
            # Returning the image URLs as a JSON response
            return JsonResponse({'image_urls': image_urls})
        else:
            # Handle other status codes
            return JsonResponse({'error': 'Failed to fetch images'}, status=response.status_code)

    except Exception as e:
        return JsonResponse({'errornlk': str(e)})
