import logging
from os import getenv
from pathlib import Path

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings

# Environment Configuration
IS_DEBUG: bool = getenv('IS_DEBUG', '').lower() in ('true', '1')
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Directory Configuration
BASE_DIR = Path(__file__).parent

if IS_DEBUG:
    from rich.logging import Console, RichHandler

    logging.basicConfig(
        format='[%(module)s.%(funcName)s:%(lineno)d]: %(message)s',
        level=logging.DEBUG,
        handlers=[RichHandler(rich_tracebacks=True, console=Console(width=150))],
        datefmt=LOG_DATE_FORMAT,
    )
else:
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s',
        level=logging.INFO,
        datefmt=LOG_DATE_FORMAT,
    )


class Settings(BaseSettings):
    PROJECT_NAME: str = 'PDF Font Analyzer'
    API_PORT: int = 8000
    IS_DEBUG: bool = False
    ALLOWED_HOSTS: list[AnyHttpUrl] = []

    class Config:
        case_sensitive = True
        env_ignore_empty = True


settings = Settings()
