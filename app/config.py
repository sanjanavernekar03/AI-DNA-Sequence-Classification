import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dna-ai-admin-secret-change-this-in-production"
    )

    DEBUG = os.getenv("FLASK_DEBUG", "1").lower() in {"1", "true", "yes"}
    PORT = int(os.getenv("PORT", "5000"))

    # MySQL Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME", "ai_dna_merged_project")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "s8197")

    # Admin credentials are used only to bootstrap the local admin account.
    # The password is hashed before it is stored in SQLite.
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@12345")

    UPLOAD_FOLDER = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")

    GENERATED_REPORTS_FOLDER = BASE_DIR / os.getenv(
        "GENERATED_REPORTS_FOLDER",
        "generated_reports"
    )

    MODELS_DIR = BASE_DIR / "app" / "ml" / "models"
    DATASET_DIR = BASE_DIR / "dataset"

    MAX_CONTENT_LENGTH = int(
        os.getenv(
            "MAX_CONTENT_LENGTH",
            str(16 * 1024 * 1024)
        )
    )

    ALLOWED_EXTENSIONS = {
        "txt",
        "fasta",
        "fa",
        "fna",
        "dna"
    }

    CHATBOT_API_KEY = os.getenv("CHATBOT_API_KEY", "")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    VOICE_API_KEY = os.getenv("VOICE_API_KEY", "")

    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_PERMANENT = False


for folder in (
    Config.UPLOAD_FOLDER,
    Config.GENERATED_REPORTS_FOLDER,
    Config.MODELS_DIR,
    Config.DATASET_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)