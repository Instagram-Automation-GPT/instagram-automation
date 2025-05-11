import os
from dotenv import load_dotenv


load_dotenv()


def get(name):
    return os.getenv(name)
