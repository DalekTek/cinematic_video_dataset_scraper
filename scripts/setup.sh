#!/bin/bash
"""
Скрипт для настройки окружения.
"""

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание необходимых директорий
mkdir -p dataset temp logs

# Копирование примера переменных окружения
cp .env.example .env

echo "Setup completed! Please edit .env file with your API keys."
