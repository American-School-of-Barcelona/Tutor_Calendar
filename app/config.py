import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from config/.env
env_path = Path(__file__).resolve().parents[1] / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

# Get the project root directory (one level up from app/)
project_root = Path(__file__).resolve().parents[1]
instance_dir = project_root / 'instance'
instance_dir.mkdir(exist_ok=True)  # Create instance directory if it doesn't exist
db_path = instance_dir / 'app.db'

class Config:
    # Secret key for session management
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration - use absolute path
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_SUBJECT_PREFIX = os.getenv('MAIL_SUBJECT_PREFIX', '[Tutomatics] ')