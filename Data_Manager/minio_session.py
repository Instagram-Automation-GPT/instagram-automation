from minio import Minio
from urllib3.exceptions import ResponseError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MinIO server information from environment variables
minio_host = os.getenv('MINIO_HOST', 'minio:9000')
minio_access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
minio_secret_key = os.getenv('MINIO_SECRET_KEY', 'miniosecret')
use_ssl = os.getenv('MINIO_USE_SSL', 'false').lower() == 'true'
bucket_name = os.getenv('MINIO_BUCKET_NAME', 'josef')

# Initialize MinIO client
minio_client = Minio(minio_host, 
                    access_key=minio_access_key,
                    secret_key=minio_secret_key, 
                    secure=use_ssl)

try:
    # Check if the bucket already exists
    bucket_exists = minio_client.bucket_exists(bucket_name)
    if not bucket_exists:
        # Create the bucket if it doesn't exist
        minio_client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")
    else:
        print(f"Bucket '{bucket_name}' already exists.")

except ResponseError as err:
    print(f"Error: {err}")


def get_minio_session():
    return minio_client
