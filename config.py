from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    gemini_api_key: str
    app_name: str = "NeoRetail Automation Hub"
    debug: bool = False


settings = Settings()  # type: ignore[call-arg]
