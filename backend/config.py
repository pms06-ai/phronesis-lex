"""
Phronesis LEX Backend Configuration
Environment-based configuration with sensible defaults
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DB_DIR = DATA_DIR / "db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_DIR}/phronesis.db")
DATABASE_PATH = DB_DIR / "phronesis.db"

# Anthropic Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

# Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "8192"))

# Server
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")

# Document Processing
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(100 * 1024 * 1024)))  # 100MB
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".doc", ".txt", ".jpg", ".jpeg", ".png", ".tiff", ".mp3", ".wav", ".m4a"]

# OCR Settings
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng")

# Analysis Settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "50000"))  # Characters per Claude call
OVERLAP_SIZE = int(os.getenv("OVERLAP_SIZE", "1000"))  # Overlap between chunks
