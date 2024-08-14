from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    MARVIN_OPENAI_API_KEY: str
    MARVIN_LOG_LEVEL: str
    model_config = SettingsConfigDict(env_file=".env")
