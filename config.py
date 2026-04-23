from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    my_phone_number: str
    dad_phone_number: str
    vapi_api_key: str
    vapi_phone_number_id: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()