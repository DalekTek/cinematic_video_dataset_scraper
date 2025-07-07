from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class VideoMetadata:
    """
    Структура для хранения метаданных видеофайла.
    """
    title: str
    url: str
    duration: float
    source: str  # 'youtube', 'vimeo', 'tiktok', 'instagram'
    category: str
    file_path: Optional[str] = None
    hash_value: Optional[str] = None
    cookies_file: Optional[Path] = None  # Путь к специфичному файлу cookies

class IVideoDownloader(ABC):
    """
    Интерфейс для скачивания видео.
    """
    @abstractmethod
    async def download_video(self, url: str, output_path: str, cookies_file: Optional[Path]) -> bool:
        """
        Скачивает видео по URL.

        Args:
            url: URL видео.
            output_path: Путь для сохранения файла.
            cookies_file: Путь к файлу cookies.

        Returns:
            True, если скачивание успешно.
        """
        pass

class IVideoProcessor(ABC):
    """
    Интерфейс для обработки видео.
    """
    @abstractmethod
    async def process_video(self, input_path: str, output_path: str) -> bool:
        """
        Обрабатывает видеофайл (например, обрезает).

        Args:
            input_path: Путь к исходному файлу.
            output_path: Путь для сохранения обработанного файла.

        Returns:
            True, если обработка успешна.
        """
        pass

class IVideoValidator(ABC):
    """
    Интерфейс для валидации видео.
    """
    @abstractmethod
    async def validate_video(self, video_path: str) -> bool:
        """
        Валидирует видеофайл.

        Args:
            video_path: Путь к видеофайлу.

        Returns:
            True, если видео прошло валидацию.
        """
        pass

class IVideoSearcher(ABC):
    """
    Интерфейс для поиска видео.
    """
    @abstractmethod
    async def search_videos(self, query: str, limit: int) -> List[VideoMetadata]:
        """
        Ищет видео по запросу.

        Args:
            query: Поисковый запрос.
            limit: Максимальное количество результатов.

        Returns:
            Список объектов VideoMetadata.
        """
        pass