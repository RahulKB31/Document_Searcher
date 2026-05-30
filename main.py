import os
from logger import setup_logger
from data_loader import load_data
from data_preprocessing import process_directory


def main():
    # Define directories
    BASE_DIR = r"C:\Users\y7rbasav\OneDrive - Carl Zeiss AG\Desktop\Document_Search"
    BAD_DIR = os.path.join(BASE_DIR, "bad_data")
    GOOD_DIR = os.path.join(BASE_DIR, "good_data")
    LOG_PATH = os.path.join(BASE_DIR, "main_process.log")

    # Setup logger
    logger = setup_logger(LOG_PATH)
    logger.info("=== Pipeline Start ===")

    # Load/refresh data
    logger.info("Starting data loading step...")
    load_data(BAD_DIR, logger)
    logger.info("Raw data loaded.")

    # Clean & process data
    logger.info("Starting data preprocessing step...")
    process_directory(BAD_DIR, GOOD_DIR, logger)
    logger.info("Data preprocessing complete.")

    logger.info("=== Pipeline End ===")


if __name__ == '__main__':
    main()