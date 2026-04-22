"""Configuration module for the trading bot.

Handles API credentials and base URL configuration using environment variables.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


@dataclass(frozen=True)
class Config:
    """Application configuration container.
    
    Attributes:
        api_key: Binance API key for authentication
        api_secret: Binance API secret for request signing
        base_url: Binance Futures Testnet base URL
        recv_window: Request receive window in milliseconds
    """
    api_key: str
    api_secret: str
    base_url: str = "https://testnet.binance.vision"
    recv_window: int = 5000


def load_config() -> Config:
    """Load configuration from environment variables.
    
    Required environment variables:
        - BINANCE_API_KEY: Your Binance API key
        - BINANCE_API_SECRET: Your Binance API secret
    
    Returns:
        Config object with loaded credentials
    
    Raises:
        ValueError: If required environment variables are not set
    """
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    
    if not api_key:
        raise ValueError(
            "BINANCE_API_KEY environment variable is not set. "
            "Please set your Binance API key."
        )
    
    if not api_secret:
        raise ValueError(
            "BINANCE_API_SECRET environment variable is not set. "
            "Please set your Binance API secret."
        )
    
    return Config(
        api_key=api_key,
        api_secret=api_secret,
        base_url="https://testnet.binance.vision",
        recv_window=5000
    )


def validate_credentials(config: Config) -> bool:
    """Validate that credentials are properly configured.
    
    Args:
        config: Configuration object to validate
    
    Returns:
        True if credentials are valid, False otherwise
    """
    return bool(config.api_key and config.api_secret and len(config.api_key) > 10)
