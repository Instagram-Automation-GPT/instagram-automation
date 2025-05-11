import pymongo
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read environment variables
MONGO_HOST = os.environ.get("MONGO_HOST", "my-mongo")  # Use container name in Docker
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))  # Use internal port
MONGO_USERNAME = os.environ.get("MONGO_INITDB_ROOT_USERNAME", "admin")
MONGO_PASSWORD = os.environ.get("MONGO_INITDB_ROOT_PASSWORD", "secretpassword")
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "josef")

# Build the MongoDB URI
mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"

# Create the MongoDB client
mongo_client = pymongo.MongoClient(mongo_uri)

# Access a specific database
db = mongo_client[MONGO_DATABASE]

def get_mongo_session():
    return db
