from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_http_methods
from django.core.files.storage import default_storage
from django.utils.text import slugify
from datetime import datetime
import os
from django.contrib.auth.decorators import login_required
# import image_editor
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.conf import settings
from Data_Manager import save
from django.contrib import admin
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Constants
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Helper functions
def is_allowed_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def validate_file_size(file):
    return file.size <= MAX_FILE_SIZE

# Views
@login_required
def index(request):
    return render(request, 'dashboard/dashboard.html')

@login_required
def register_page(request):
    return render(request, 'register.html')

@login_required
def queues_page(request):
    return render(request, 'queue.html')

@login_required
def queue_details(request):
    return render(request, 'queue_details.html')

@login_required
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')

@login_required
def publish(request):
    return render(request, 'publish/publish.html')

@login_required
def follow(request):
    return render(request, 'follower/follow.html')

@login_required
def do_follow(request):
    return render(request, 'follow/dofollow.html')

@login_required
def auto_page(request):
    return render(request, 'auto_page.html')

@login_required
@require_POST
def upload_photo(request):
    try:
        text = request.POST.get('text', '').strip()
        username = request.user.username
        photo_file = request.FILES.get('photo')

        # Validate input
        if not photo_file:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        if not text:
            return JsonResponse({'error': 'Text is required'}, status=400)

        # Validate file
        if not is_allowed_file(photo_file.name):
            return JsonResponse({'error': 'Invalid file type. Allowed types: JPG, JPEG, PNG, GIF'}, status=400)
        
        if not validate_file_size(photo_file):
            return JsonResponse({'error': f'File size exceeds {MAX_FILE_SIZE/1024/1024}MB limit'}, status=400)

        # Create storage directory if it doesn't exist
        storage_dir = os.path.join(settings.MEDIA_ROOT, 'storage')
        os.makedirs(storage_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{slugify(username)}_{timestamp}{os.path.splitext(photo_file.name)[1]}"
        photo_path = os.path.join('storage', safe_filename)
        normalized_photo_path = os.path.normpath(photo_path)

        # Save file
        with default_storage.open(photo_path, 'wb+') as destination:
            for chunk in photo_file.chunks():
                destination.write(chunk)

        # Process image (commented out as per original)
        current_time = datetime.now()
        outputs = []
        # gradient_outputs = image_editor.add_text_to_image(photo_path, text, "fonts/Calibri.ttf", "gradient", current_time)
        # psd_outputs = image_editor.add_text_to_image(photo_path, text, "fonts/Calibri.ttf", "psd", current_time)
        # outputs.extend(gradient_outputs)
        # outputs.extend(psd_outputs)

        # Save generated content
        flag, urls = save.save_generated(outputs, username, current_time)
        
        # Clean up
        try:
            if os.path.exists(normalized_photo_path):
                os.remove(normalized_photo_path)
        except OSError as e:
            logger.error(f"Error removing temporary file {normalized_photo_path}: {e}")

        if flag == "OK":
            return JsonResponse({'message': urls}, status=200)
        else:
            return JsonResponse({'error': f"Processing error: {urls}"}, status=400)

    except Exception as e:
        logger.error(f"Error in upload_photo: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@require_http_methods(["GET", "POST"])
def login_account(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required')
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')

    return render(request, 'login.html')
