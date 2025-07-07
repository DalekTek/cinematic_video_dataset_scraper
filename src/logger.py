import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Настраивает систему логирования для вывода в консоль и файл.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR).
        log_file: Имя файла для записи логов.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file_path = log_dir / (log_file or "video_collector.log")

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Настройка корневого логгера
    root_logger = logging.getLogger()
    # Устанавливаем уровень на самый низкий, чтобы обработчики могли фильтровать
    root_logger.setLevel(logging.DEBUG)

    # Удаление существующих обработчиков, чтобы избежать дублирования
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level.upper())
    root_logger.addHandler(console_handler)

    # Файловый обработчик
    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG) # В файл пишем все, начиная с DEBUG
    root_logger.addHandler(file_handler)

    logging.info(f"Logging setup complete. Level: {log_level}. Log file: {log_file_path}")