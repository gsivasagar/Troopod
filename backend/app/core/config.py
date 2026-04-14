"""
Configuration Module
Centralizes environment variables and application settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration."""
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "2"))
    
    @classmethod
    def validate(cls):
        """Validate critical configurations."""
        if not cls.GEMINI_API_KEY or cls.GEMINI_API_KEY == "your_gemini_api_key_here":
            raise ValueError("GEMINI_API_KEY is not set in environment variables. Please check your .env file.")

# Validate on import
try:
    Config.validate()
except ValueError as e:
    print(f"Warning: {e}")

config = Config()
