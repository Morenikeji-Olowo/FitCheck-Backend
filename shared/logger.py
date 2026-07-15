import logging
from core.config.settings import settings

class Environment:
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for any module — pass __name__"""

    logger = logging.getLogger(name)

    if not logger.handlers:
        handlers = [logging.StreamHandler()]

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        level = (
            logging.DEBUG 
            if settings.ENV == Environment.DEVELOPMENT 
            else logging.INFO
        )
        logger.setLevel(level)
        logger.propagate = False

    return logger