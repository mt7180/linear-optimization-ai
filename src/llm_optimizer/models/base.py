from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    OPENAI_API_KEY: str
    LOG_LEVEL: str
    model_config = SettingsConfigDict(env_file=".env")


class InvalidInputError(Exception):
    def __init__(self, message="Invalid input provided."):
        self.message = message
        super().__init__(self.message)
