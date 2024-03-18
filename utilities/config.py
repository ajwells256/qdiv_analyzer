import sys
from datetime import datetime
from logging import getLogger, StreamHandler, Formatter, FileHandler


def configure_logger():
    root_logger = getLogger()
    print_handler = StreamHandler(sys.stdout)
    file_handler = FileHandler(f"seclog_{datetime.now().strftime('%Y-%m-%d_%H:%M')}.log")
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(print_handler)
    root_logger.addHandler(file_handler)
