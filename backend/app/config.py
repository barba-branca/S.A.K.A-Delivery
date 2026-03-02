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
    
    # Database (PostgreSQL async)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/saka_delivery"
    )
    
    # Sync database URL for Alembic (auto-generated from async URL)
    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("+asyncpg", "")
    
    # CORS
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "saka-delivery-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h
    
    # Gemini AI
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # MercadoPago
    mercadopago_public_key: str = os.getenv("MERCADOPAGO_PUBLIC_KEY", "")
    mercadopago_access_token: str = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
    mercadopago_webhook_secret: str = os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "")
    
    # Configurações de retry para webhook
    webhook_max_retries: int = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))
    webhook_retry_delay: int = int(os.getenv("WEBHOOK_RETRY_DELAY", "5"))
    
    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
