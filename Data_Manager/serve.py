from mimetypes import guess_type
from . import minio_session
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from urllib3.exceptions import ResponseError
from urllib.parse import unquote

client = minio_session.get_minio_session()


@require_GET
def serve_minio_image(request, path):
    try:
        decoded_path = unquote(path)
        # Fetch the image from MinIO
        image_data = client.get_object('josef', decoded_path)  # Replace 'bucket_name' with your MinIO bucket name

        # Determine the content type based on the file extension
        content_type, _ = guess_type(decoded_path)
        if content_type is None:
            content_type = 'application/octet-stream'  # Default to binary data if content type cannot be determined

        # Return the image as an HTTP response
        return HttpResponse(image_data.read(), content_type=content_type)

    except ResponseError as err:
        return HttpResponse(status=404)  # Return 404 if the image is not found or there's an error

@require_GET
def serve_minio_video(request, path):
    try:
        decoded_path = unquote(path)
        video_data = client.get_object('josef', decoded_path)  # Replace 'josef' with your bucket name
        
        content_type, _ = guess_type(decoded_path)
        if content_type is None:
            content_type = 'video/mp4'  # Default to MP4

        response = StreamingHttpResponse(video_data, content_type=content_type)
        response['Accept-Ranges'] = 'bytes'  # Enables seeking in video
        response['Content-Disposition'] = f'inline; filename="{decoded_path}"'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except ResponseError:
        return HttpResponse(status=404)