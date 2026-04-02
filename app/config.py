import os
from dotenv import load_dotenv

load_dotenv()

# Database Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ai_poster_db")

# APIs
SD_API_URL = os.getenv("SD_API_URL", "http://127.0.0.1:7860/sdapi/v1/txt2img")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MOCK_SD = os.getenv("MOCK_SD", "false").lower() == "true"
USE_POLLINATIONS = os.getenv("USE_POLLINATIONS", "false").lower() == "true"
HF_API_KEY = os.getenv("HF_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Instagram Credentials
IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_PASSWORD = os.getenv("IG_PASSWORD", "")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://www.instagram.com/")
CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH", "") # Path to Chrome user data directory
