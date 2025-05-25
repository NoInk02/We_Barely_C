import os


# ENV path
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

# Load environment variables
class Settings():
    MONGO_URI = 'mongodb+srv://Cobaltboy:Temp1234@devhack-team-atom.cfskp.mongodb.net/?retryWrites=true&w=majority&appName=DevHack-Team-Atom'
    MASTER_DB_NAME = 'flipr-hackathon'
    ADMIN_LIST = 'admin_list'
    COMPANY_LIST = 'company_list'
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    JWT_SECRET_KEY = '9fsXWIn4SbNpqrpanTN8NnhfcuaE5dXjP5hlH1jW1WU4Yj76RNIloC7vNWDlOdrr'
    GEMINI_API_KEY = "AIzaSyCSypgJaG3XLvlJvbDg_kg5RbzZm4vf9B8"


settings = Settings()