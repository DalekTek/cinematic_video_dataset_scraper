import asyncio
import json
import subprocess
from typing import List

from .base_searcher import BaseSearcher
from ..interfaces import VideoMetadata
from ..config import Config
from ..exceptions import DownloadError


class YouTubeSearcher(BaseSearcher):
    """
    Класс для поиска видео на YouTube с использованием yt-dlp.
    """

    def __init__(self, config: Config):
        super().__init__(config, 'youtube')

    def _sync_search(self, query: str, limit: int) -> str:
        """
        Синхронная функция для запуска yt-dlp, которую мы будем выполнять в отдельном потоке.
        """
        search_query = f"ytsearch{limit}:{query}"
        cmd = [
            'yt-dlp', '--dump-json', '--flat-playlist', '--quiet',
            '--force-ipv4', search_query
        ]
        # Используем стандартный subprocess.run, который является блокирующим
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

        if result.returncode != 0:
            raise DownloadError(f"yt-dlp search failed with code {result.returncode}: {result.stderr}")

        return result.stdout

    async def search_videos(self, query: str, limit: int) -> List[VideoMetadata]:
        """
        Выполняет поиск видео на YouTube, запуская блокирующий вызов в отдельном потоке.
        """
        self.logger.info(f"Searching YouTube for '{query}' with limit {limit}")
        results = []
        try:
            # Запускаем синхронную функцию в потоке, чтобы не блокировать event loop
            loop = asyncio.get_running_loop()
            stdout = await loop.run_in_executor(None, self._sync_search, query, limit)

            for line in stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    video_info = json.loads(line)
                    if 'duration' in video_info and video_info['duration'] is not None:
                        results.append(VideoMetadata(
                            title=video_info.get('title', 'Untitled YouTube Video'),
                            url=video_info.get('url'),
                            duration=float(video_info.get('duration')),
                            source="youtube",
                            category=self._categorize_video(query),
                            cookies_file=self.cookies_path
                        ))
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    self.logger.warning(f"Could not parse YouTube video metadata: {e}. Line: '{line[:100]}...'")

        except FileNotFoundError:
            self.logger.critical(
                "yt-dlp command not found. Please ensure yt-dlp is installed and accessible in your system's PATH."
            )
            return []
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during YouTube search for '{query}': {e}", exc_info=True)
            return []

        self.logger.info(f"Found {len(results)} videos on YouTube for query '{query}'.")
        return results