import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde el directorio de backend
base_dir = Path(__file__).resolve().parent
dotenv_path = base_dir / ".env"
load_dotenv(dotenv_path)


class Config:
    # Supabase / PostgreSQL configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")
    SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    # Fallback MySQL‑style variables for local dev (if you still want them)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 5000))
    JWT_SECRET = os.getenv("JWT_SECRET", "huellitas_felices_secret_key_2026")
    JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", 8))
    API_KEY = os.getenv("API_KEY", "huellitas_api_secret_key_2026")
