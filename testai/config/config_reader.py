

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    bot_token: str
    openai_key: str
    database_url: str

    def get_sqlalchemy_database_url(self) -> str:
        return self.database_url.replace("postgresql", "postgresql+asyncpg")


def get_config() -> Config:
    return Config(_env_file='.env', _env_file_encoding='utf-8')
