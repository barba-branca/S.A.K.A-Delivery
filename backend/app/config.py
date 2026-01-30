"""
Configurações do servidor backend.
Carrega variáveis de ambiente e define configurações globais.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""
    
    # iFood API
    ifood_client_id: str = os.getenv("IFOOD_CLIENT_ID", "")
    ifood_client_secret: str = os.getenv("IFOOD_CLIENT_SECRET", "")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./orders.db")
    
    # CORS
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
