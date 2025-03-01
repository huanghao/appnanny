import os


class Config:
    # Base configuration
    HOST = "0.0.0.0"
    PORT = 5000

    # App storage and metadata
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STORAGE_PATH = os.path.join(BASE_DIR, "apps")
    METADATA_FILE = "apps_metadata.json"

    # Logging
    LOG_FILE = "appnanny.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_LEVEL = "INFO"
    LOG_MAX_BYTES = 2_000_000  # 2MB
    LOG_BACKUP_COUNT = 2

    # Port allocation
    PORT_RANGES = [
        range(8080, 8090),  # For web apps
        range(4040, 4050),  # For additional services
    ]

    # Supported app types and commands
    APP_TYPES = {
        "streamlit": ["streamlit", "run"],
        "voila": ["voila"],
        "flask": ["python"],
        "fastapi": ["python"],
        "gradio": ["python"],
    }


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "INFO"


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "INFO"
    PORT = 8000


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    STORAGE_PATH = os.path.join(Config.BASE_DIR, "test_apps")


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

# Get current configuration
active_config = config[os.getenv("FLASK_ENV", "default")]
