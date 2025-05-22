import os
from dotenv import load_dotenv


# ENV path
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

env = load_dotenv(env_path)

# Load environment variables
class Settings():
    MONGO_URI = os.getenv("MONGO_HOST")
    MASTER_DB_NAME = os.getenv("MASTER_DB_NAME")
    ADMIN_LIST = os.getenv("ADMIN_TABLE_NAME")
    ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


settings = Settings()