from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="Novel2Script AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    ai_provider: str = Field(default="mock", alias="AI_PROVIDER")
    ai_model: str = Field(default="deepseek-chat", alias="AI_MODEL")  # backward compatible
    ai_chat_model: str = Field(default="deepseek-chat", alias="AI_CHAT_MODEL")
    ai_pro_model: str = Field(default="deepseek-reasoner", alias="AI_PRO_MODEL")
    ai_api_key: str = Field(default="", alias="AI_API_KEY")
    ai_base_url: str = Field(default="https://api.deepseek.com/v1", alias="AI_BASE_URL")
    ai_timeout: int = Field(default=90, alias="AI_TIMEOUT")

    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    trace_enabled: bool = Field(default=True, alias="TRACE_ENABLED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
