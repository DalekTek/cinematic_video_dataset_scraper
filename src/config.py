import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import logging

from .exceptions import ConfigError


@dataclass
class Config:
    """
    Конфигурация системы сбора видео, загружаемая из переменных окружения.
    """
    # API ключи
    rapidapi_key: str = None

    # Основные параметры
    target_videos_count: int = 1000
    max_video_duration: int = 5
    min_video_duration: int = 1

    # Пути
    base_output_dir: Path = Path("dataset")
    temp_dir: Path = Path("temp")
    cookies_dir: Path = Path("cookies")

    # Настройки производительности
    max_concurrent_downloads: int = 5
    request_timeout: int = 30
    retry_attempts: int = 3

    # Источники и категории
    sources: List[str] = field(default_factory=list)
    video_categories: List[str] = field(default_factory=list)

    # Пути к файлам cookies
    youtube_cookies: Optional[Path] = None
    vimeo_cookies: Optional[Path] = None
    tiktok_cookies: Optional[Path] = None
    instagram_cookies: Optional[Path] = None

    def __post_init__(self):
        """
        Инициализация и валидация конфигурации после создания объекта.
        """
        logger = logging.getLogger(__name__)

        self.rapidapi_key = os.getenv("RAPIDAPI_KEY")
        if not self.rapidapi_key:
            raise ConfigError("RAPIDAPI_KEY is not set in environment variables. Please check your .env file.")

        self.target_videos_count = int(os.getenv("TARGET_VIDEOS_COUNT", "100"))
        self.max_video_duration = int(os.getenv("MAX_VIDEO_DURATION", "5"))
        self.min_video_duration = int(os.getenv("MIN_VIDEO_DURATION", "1"))
        self.max_concurrent_downloads = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "5"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.retry_attempts = int(os.getenv("RETRY_ATTEMPTS", "3"))

        sources_str = os.getenv("SOURCES", "youtube,vimeo,tiktok,instagram")
        self.sources = [s.strip() for s in sources_str.split(',') if s.strip()]

        self.youtube_cookies = self._get_cookie_path("YOUTUBE_COOKIES", "youtube-cookies.txt")
        self.vimeo_cookies = self._get_cookie_path("VIMEO_COOKIES", "vimeo-cookies.txt")
        self.tiktok_cookies = self._get_cookie_path("TIKTOK_COOKIES", "tiktok-cookies.txt")
        self.instagram_cookies = self._get_cookie_path("INSTAGRAM_COOKIES", "instagram-cookies.txt")

        self._validate_cookies(logger)

        self.video_categories = [
            "explosions", "neon", "smoke", "camera-move",
            "transformations", "action-scenes"
        ]

        self._create_directories()

    def _get_cookie_path(self, env_var: str, default_filename: str) -> Path:
        """Получает путь к файлу cookies из .env или использует путь по умолчанию."""
        path_str = os.getenv(env_var, str(self.cookies_dir / default_filename))
        return Path(path_str)

    def _validate_cookies(self, logger: logging.Logger) -> None:
        """Проверяет существование файлов cookies и логирует предупреждения."""
        for source in self.sources:
            if source == "youtube": continue

            cookie_path = getattr(self, f"{source}_cookies", None)
            if not cookie_path or not cookie_path.exists():
                logger.warning(
                    f"Cookies file for '{source}' not found at '{cookie_path}'. This source may not work correctly.")
            elif cookie_path.stat().st_size == 0:
                logger.warning(f"Cookies file for '{source}' is empty: '{cookie_path}'.")

    def _create_directories(self) -> None:
        """Создает все необходимые для работы директории."""
        self.base_output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        self.cookies_dir.mkdir(exist_ok=True)

        for category in self.video_categories:
            (self.base_output_dir / category).mkdir(exist_ok=True)