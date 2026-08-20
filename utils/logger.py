import logging, os

def setup_logger():
    os.makedirs('logs', exist_ok=True)
    logger = logging.getLogger('WindowsMacroRecorder')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

    file_handler = logging.FileHandler('logs/macro_recorder.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()