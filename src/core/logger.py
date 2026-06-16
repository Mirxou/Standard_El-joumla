"""
Logger module
"""
import logging


# Create a logger
logger = logging.getLogger("eljoumla")
logger.setLevel(logging.INFO)

# Create console handler
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
