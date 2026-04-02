from src.bootstrap.app_factory import create_app
from src.bootstrap.logging_config import setup_logging

setup_logging()
app = create_app()