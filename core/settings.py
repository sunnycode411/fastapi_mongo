import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

# Database Settings 
DATABASE_URI = os.getenv("DATABASE_URI", "mongodb://localhost:27017/")
DATABASE = os.getenv("DATABASE", "default_db")

# Logging Settings
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
LOGGING_FORMAT = os.getenv("LOGGING_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Directories Settings
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / os.getenv("LOGS_PATH", "logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = PROJECT_ROOT / os.getenv("DATA_PATH", "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR = PROJECT_ROOT / os.getenv("TEMP_PATH", "temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
TEST_DIR = PROJECT_ROOT / os.getenv("TEST_PATH", "test")
TEST_DIR.mkdir(parents=True, exist_ok=True)
