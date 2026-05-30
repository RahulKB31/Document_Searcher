import logging
import os

def setup_logger(log_path):
    logger = logging.getLogger('DataExportLogger')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    # File Handler
    if not logger.handlers:
        fh = logging.FileHandler(log_path, mode='a')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Console Handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger