from pymongo.errors import DuplicateKeyError
from . import minio_session
from . import mongo_session
from urllib3.exceptions import ResponseError

minio_client = minio_session.get_minio_session()
bucket_name = 'josef'
db = mongo_session.get_mongo_session()
collection = db["Images"]
collection.create_index([("path", 1)], unique=True)


def save_generated(outputs, username, current_time):

    # Upload image to the specified folder in the bucket
    formatted_time = current_time.strftime("%Y-%m-%d %H%M%S")
    file_formatted_time = current_time.strftime("%Y-%m-%d %H%M%S")
    folder_name = outputs[0].split("/")[-1].split("_")[0] + f" {file_formatted_time}"
    document = {
        "username": username,
        "path": folder_name,
        "timestamp": formatted_time,
        "generated": True
    }
    try:
        result = collection.insert_one(document)
        # Check if the insertion was successful
        if not result.inserted_id:
            return "Error", "Failed to insert document in DB!"
    except DuplicateKeyError:
        return "Error", "Duplicate path found in the database. Path must be unique."
    urls = []
    for image in outputs:
        object_name = folder_name + "/" + image.split("/")[-1]
        try:
            minio_client.fput_object(bucket_name, object_name, image)
            urls.append(object_name)
        except ResponseError as error:
            return "Error", "Failed to save images in Minio!"

    return "OK", urls
