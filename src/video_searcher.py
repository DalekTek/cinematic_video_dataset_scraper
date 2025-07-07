# src/video_searcher.py
import asyncio
import logging
import random
from typing import List, Dict, Type
import importlib

from .interfaces import IVideoSearcher, VideoMetadata
from .config import Config


class VideoSearcher(IVideoSearcher):
    """
    Агрегатор, который выполняет поиск видео по всем настроенным источникам.
    """
    SOURCE_MAP = {
        "youtube": ("src.sources.youtube_searcher", "YouTubeSearcher"),
        "vimeo": ("src.sources.vimeo_searcher", "VimeoSearcher"),
        "tiktok": ("src.sources.tiktok_searcher", "TikTokSearcher"),
        "instagram": ("src.sources.instagram_searcher", "InstagramSearcher"),
    }

    def __init__(self, config: Config):
        """
        Инициализация поисковика-агрегатора.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.searchers = self._init_searchers()
        if not self.searchers:
            self.logger.critical("No video searchers were initialized. "
                                 "Check your 'SOURCES' environment variable and logs for errors.")

    def _init_searchers(self) -> Dict[str, IVideoSearcher]:
        """
        Динамически инициализирует поисковики для активных источников.
        """
        searchers = {}
        for source_name in self.config.sources:
            if source_name in self.SOURCE_MAP:
                module_name, class_name = self.SOURCE_MAP[source_name]
                try:
                    module = importlib.import_module(module_name)
                    searcher_class: Type[IVideoSearcher] = getattr(module, class_name)
                    searchers[source_name] = searcher_class(self.config)
                    self.logger.info(f"Successfully initialized searcher for '{source_name}'.")
                except (ImportError, AttributeError) as e:
                    self.logger.error(f"Failed to initialize '{source_name}' searcher: {e}")
            else:
                self.logger.warning(f"Unsupported source '{source_name}' found in config.")
        return searchers

    async def search_videos(self, query: str, limit: int) -> List[VideoMetadata]:
        """
        Асинхронно выполняет поиск по всем активным источникам.
        """
        if not self.searchers:
            return []

        limit_per_source = max(1, limit // len(self.searchers))

        tasks = [
            searcher.search_videos(query, limit_per_source)
            for searcher in self.searchers.values()
        ]

        results_from_sources = await asyncio.gather(*tasks, return_exceptions=True)

        all_videos = []
        for i, result in enumerate(results_from_sources):
            source_name = list(self.searchers.keys())[i]
            if isinstance(result, Exception):
                self.logger.error(f"Search task for source '{source_name}' failed: {result}")
            elif result:
                all_videos.extend(result)

        random.shuffle(all_videos)
        self.logger.info(f"Total videos found for query '{query}' across all sources: {len(all_videos)}")
        return all_videos[:limit]

    def _categorize_video(self, query: str) -> str:
        # Этот метод не используется в агрегаторе, так как категоризация
        # происходит в конкретных поисковиках.
        pass