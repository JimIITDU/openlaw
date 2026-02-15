import os
from dotenv import load_dotenv
from typing import Optional

class Config:
    """Centralized configuration management for ConstitutionBD"""
    
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # API Keys
        self.OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
        
        # LLM Configuration
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")
        self.MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-1.5-flash")
        self.TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
        self.MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
        
        # Embedding Configuration
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        # RAG Configuration
        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
        
        # Vector Database Configuration
        self.VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./chroma_db")
        self.COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "constitution_collection")
        
        # Server Configuration
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate essential configuration"""
        if self.LLM_PROVIDER == "google" and not self.GOOGLE_API_KEY:
            print("Warning: GOOGLE_API_KEY not set for Google LLM provider")
        elif self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            print("Warning: OPENAI_API_KEY not set for OpenAI LLM provider")
        elif self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            print("Warning: ANTHROPIC_API_KEY not set for Anthropic LLM provider")

# Global config instance
config = Config()
