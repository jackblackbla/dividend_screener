# config/__init__.py
import os
from dotenv import load_dotenv

# Load .env file from config directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading .env from: {env_path}")  # .env 파일 경로 로깅
load_dotenv(env_path)

DART_API_KEY = os.getenv('DART_API_KEY')
print(f"DART_API_KEY loaded: '{DART_API_KEY}' (length={len(DART_API_KEY) if DART_API_KEY else 0})")  # API 키 로깅 추가