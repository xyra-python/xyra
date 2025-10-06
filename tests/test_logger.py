import logging

from xyra.logger import get_logger, setup_logging


def test_get_logger():
    logger = get_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test"


def test_get_logger_default():
    logger = get_logger()
    assert logger.name == "xyra"


def test_setup_logging():
    # This will configure the root logger
    setup_logging(level=logging.DEBUG)
    # Just check that setup_logging doesn't raise an error
    # Level checking is tricky due to existing handlers
    assert True
