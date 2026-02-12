"""
Provide configuration settings for the agent app.

Pull settings from environment variables or a .env file if available.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Provide a pydantic ``BaseSettings`` model for the application settings.
    """

    DEPLOY_ENV: str = "LOCAL"

    # Armasec authentication settings
    ARMASEC_DOMAIN: str = Field(default="armasec.dev")
    ARMASEC_USE_HTTPS: bool = Field(True)
    ARMASEC_DEBUG: bool = Field(False)
    ARMASEC_ADMIN_DOMAIN: Optional[str] = None
    ARMASEC_ADMIN_MATCH_KEY: Optional[str] = None
    ARMASEC_ADMIN_MATCH_VALUE: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
