import sys
import logging


def setup_logging(name: str = None) -> logging.Logger:
    root = logging.getLogger()
    logger = root.getChild(name) if name else root
    root.setLevel(logging.INFO)

    # Setup logging to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    root.addHandler(handler)

    return logger
