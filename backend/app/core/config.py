from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="Novel2Script AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()