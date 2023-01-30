import logging


logger = logging.getLogger('pyxmas')
logger.setLevel(logging.DEBUG)

LOG_DEBUG = logging.DEBUG
LOG_INFO = logging.INFO
LOG_WARNING = logging.WARNING
LOG_ERROR = logging.ERROR
LOG_CRITICAL = logging.CRITICAL
LOG_FATAL = logging.FATAL


def enable_logging(level:int = LOG_DEBUG, format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)

__all__ = ['logger', 'enable_logging', 'LOG_DEBUG', 'LOG_INFO', 'LOG_WARNING', 'LOG_ERROR', 'LOG_CRITICAL', 'LOG_FATAL']
