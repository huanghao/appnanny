import logging
from logging.handlers import RotatingFileHandler
from config import active_config as config

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format=config.LOG_FORMAT)

logger = logging.getLogger("appnanny")

handler = RotatingFileHandler(
    config.LOG_FILE, maxBytes=config.LOG_MAX_BYTES, backupCount=config.LOG_BACKUP_COUNT
)
handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(handler)
