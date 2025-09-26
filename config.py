# config.py

import os
from dotenv import load_dotenv

# Find the absolute path of the root directory of the project (where this file is).
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    """
    Centralizes all configuration settings for the Flask application.
    """
    
    # --- Secret Keys & API Keys ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-default-secret-key-for-dev-but-change-in-prod'
    CSC_API_KEY = os.environ.get('CSC_API_KEY')

    # --- Application Settings ---
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 't']
    
    # --- Database Configuration ---
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    
    # --- CORRECTED File Upload Configuration ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    UPLOAD_URL_PATH = 'uploads'

    # --- START: NEW EMAIL CONFIGURATION SECTION ---
    # This section has been added to support Flask-Mail for password resets.
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    # --- END: NEW EMAIL CONFIGURATION SECTION ---