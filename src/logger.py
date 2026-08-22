"""Модуль логирования приложения."""

import logging
from pathlib import Path


def setup_logger(name: str = "app", log_file: str = "logs/app.log") -> logging.Logger:
    """
    Настраивает и возвращает логгер.

    Логи записываются одновременно в файл и в консоль.

    Args:
        name: Имя логгера.
        log_file: Путь к файлу логов.

    Returns:
        Настроенный логгер.
    """
    # Создаём папку для логов
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Создаём логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Избегаем дублирования обработчиков при повторном вызове
    if logger.handlers:
        return logger

    # Формат логов
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-10s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Обработчик для записи в файл
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger