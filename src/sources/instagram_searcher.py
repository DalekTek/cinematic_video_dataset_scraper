from typing import List

from .base_searcher import BaseRapidAPISearcher
from ..interfaces import VideoMetadata
from ..config import Config


class InstagramSearcher(BaseRapidAPISearcher):
    """
    Класс для поиска видео в Instagram.
    """

    def __init__(self, config: Config):
        super().__init__(config, 'instagram')

    def _parse_results(self, data: dict, query: str) -> List[VideoMetadata]:
        """Парсит результаты ответа API для Instagram."""
        videos = []
        for item in data.get('medias', []):
            try:
                url = item.get('url')
                if not url and 'video_versions' in item and item['video_versions']:
                    url = item['video_versions'][0].get('url')

                if not url: continue

                videos.append(VideoMetadata(
                    title=item.get('title') or item.get('caption', {}).get('text') or "Instagram Video",
                    url=url,
                    duration=float(item.get('video_duration', 0)),
                    source=self.source_name,
                    category=self._categorize_video(query),
                    cookies_file=self.cookies_path
                ))
            except (KeyError, TypeError, ValueError) as e:
                self.logger.warning(f"Skipping invalid Instagram item: {e}. Raw item: {item}")

        self.logger.info(f"Parsed {len(videos)} videos from Instagram for query '{query}'.")
        return videos