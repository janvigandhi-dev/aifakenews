import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
SAVED_MODELS_DIR = BASE_DIR / "models" / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    APP_NAME: str = "TruthLens — Explainable AI Fake News Detection"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Groq API Key for Evidence Verification & Claim Extraction (read from environment or .env)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    
    # SQLite Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/truthlens.db"
    
    # Risk Score Thresholds
    RISK_THRESHOLD_LOW: float = 35.0
    RISK_THRESHOLD_HIGH: float = 65.0
    
    # Supported Models
    DEFAULT_MODEL: str = "linear_svm"
    
    # Request limits
    MAX_TEXT_LENGTH: int = 100000
    MIN_TEXT_LENGTH: int = 15

settings = Settings()
