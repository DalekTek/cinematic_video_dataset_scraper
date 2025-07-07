# Cinematic Video Dataset Collector

Система для автоматического сбора видеофрагментов из различных источников.

## Возможности

- Поиск видео по ключевым словам в YouTube, Vimeo и других источниках
- Автоматическое скачивание и обработка видео
- Валидация видео (длительность, дубликаты)
- Категоризация по типам контента
- Создание структурированного датасета
- Архивирование результатов

## Установка

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Установите FFmpeg:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Скачайте с https://ffmpeg.org/download.html
```

3. Настройте переменные окружения:

```bash
cp .env.example .env
# Отредактируйте .env файл
```

## Rapid API

Для получения Rapid API key вам нужно зарегистрироваться на RapidAPI и подключиться к API сервисам для поиска видео.
Вот пошаговая инструкция:

1. Перейдите на сайт [RapidAPI](https://rapidapi.com/).
2. Создайте аккаунт или войдите в существующий.
3. Найдите API для поиска видео,
   например, [All Media Downloader](https://rapidapi.com/andryerica1/api/all-media-downloader3).
4. Подключитесь к выбранному API, нажав кнопку "Subscribe".
5. После подписки вы получите ключ API (API Key), который нужно будет указать в файле `.env` в
   переменной `RAPID_API_KEY`.

## Приложение использует сookies браузера для доступа к некоторым видео платформам. Чтобы получить cookies:

1. Установите расширение для браузера, которое экспортирует cookies в формате Netscape. Например:
    * Для
      Chrome/Edge: [Get cookies.txt LOCALLY](https://www.google.com/url?sa=E&q=https%3A%2F%2Fchrome.google.com%2Fwebstore%2Fdetail%2Fget-cookiestxt-locally%2Fcclelndahbckbenkjhflpdbgdldlbecc)
    * Для Firefox: [cookies.txt](https://www.google.com/url?sa=E&q=https%3A%2F%2Faddons.mozilla.org%2Fen-US%2Ffirefox%2Faddon%2Fcookies-txt%2F)
2. Зайдите на [youtube](https://www.youtube.com/), [instagram](https://www.instagram.com/), [tiktok](https://www.tiktok.com/).
3. Используя расширение, экспортируйте cookies в файл. Назовите его `youtube-cookies.txt` и **поместите в корень проекта**.
4. ВАЖНО: Добавьте *.txt в ваш .gitignore, чтобы случайно не закоммитить свои личные cookies в репозиторий.

Для использования RapidAPI (All Media Downloader) нам понадобится:
- URL API: `https://all-media-downloader3.p.rapidapi.com/search/{platform}`
- Параметры: `query` (строка запроса) и `limit` (количество результатов)
- Заголовки: `X-RapidAPI-Key`, `X-RapidAPI-Host`

## Использование

```bash
python main.py
```

## Компоненты

- `VideoSearcher`: Поиск видео в различных источниках
- `VideoDownloader`: Скачивание видео
- `VideoProcessor`: Обработка видео (обрезка, конвертация)
- `VideoValidator`: Валидация видео
- `DatasetBuilder`: Создание финального датасета
- `VideoCollector`: Координация всех компонентов

## Результат

Система создает:

- Структурированный датасет с категориями
- CSV/JSON индексы с метаданными
- Статистику датасета
- ZIP-архив готовый к использованию
