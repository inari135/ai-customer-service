"""
配置管理：从 .env 文件和环境变量加载配置
"""
import os
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
load_dotenv()


class Settings:
    # --- LLM ---
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-v4-flash")

    # --- Embedding ---
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "siliconflow")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")

    # --- JWT ---
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/customer_service.db")

    # --- Server ---
    API_PORT: int = int(os.getenv("API_PORT", "8000"))


settings = Settings()
