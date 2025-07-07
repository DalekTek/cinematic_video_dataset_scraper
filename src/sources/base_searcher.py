import asyncio
import logging
from typing import Optional, Dict, Any, List
from abc import abstractmethod
import aiohttp

from ..config import Config
from ..interfaces import IVideoSearcher, VideoMetadata
from ..exceptions import APIError, RateLimitError

class BaseSearcher(IVideoSearcher):
    """
    Абстрактный базовый класс для всех поисковиков.
    """
    def __init__(self, config: Config, source_name: str):
        self.config = config
        self.logger = logging.getLogger(f"src.sources.{source_name}")
        self.source_name = source_name
        self.cookies_path = getattr(config, f"{source_name}_cookies", None)

    @abstractmethod
    async def search_videos(self, query: str, limit: int) -> List[VideoMetadata]:
        pass

    def _categorize_video(self, query: str) -> str:
        """Определение категории видео по поисковому запросу."""
        query_lower = query.lower()
        if any(word in query_lower for word in ['explosion', 'blast', 'boom']):
            return "explosions"
        if any(word in query_lower for word in ['neon', 'cyberpunk', 'glow']):
            return "neon"
        if any(word in query_lower for word in ['smoke', 'fog', 'mist']):
            return "smoke"
        if any(word in query_lower for word in ['camera', 'spin', 'movement']):
            return "camera-move"
        if any(word in query_lower for word in ['transform', 'morph', 'change']):
            return "transformations"
        return "action-scenes"

class BaseRapidAPISearcher(BaseSearcher):
    """
    Базовый класс для поисковиков, использующих 'all-media-downloader3' API.
    Исправляет ошибку 404, используя правильный эндпоинт.
    """
    API_BASE_URL = "https://all-media-downloader3.p.rapidapi.com"
    API_HOST = "all-media-downloader3.p.rapidapi.com"

    def __init__(self, config: Config, source_name: str):
        super().__init__(config, source_name)

    async def search_videos(self, query: str, limit: int) -> List[VideoMetadata]:
        """Выполняет поиск, передавая имя платформы как параметр."""
        headers = {
            "X-RapidAPI-Key": self.config.rapidapi_key,
            "X-RapidAPI-Host": self.API_HOST
        }
        full_url = f"{self.API_BASE_URL}/search/"
        full_url = full_url.replace("\\", "/")  # Исправление пути для URL

        params = {"platform": self.source_name, "query": query, "limit": limit}

        try:
            data = await self._make_api_request(full_url, headers, params)
            return self._parse_results(data, query)
        except APIError as e:
            self.logger.error(f"Failed to search {self.source_name.capitalize()} for '{query}': {e}")
            return []
        except Exception as e:
            self.logger.error(f"An unexpected error during {self.source_name.capitalize()} search: {e}", exc_info=True)
            return []

    async def _make_api_request(self, url: str, headers: Dict, params: Dict) -> Dict[str, Any]:
        cookies = self._load_cookies(self.source_name)
        for attempt in range(self.config.retry_attempts + 1):
            print(url)
            try:
                async with aiohttp.ClientSession(cookies=cookies) as session:
                    async with session.get(url, headers=headers, params=params, timeout=self.config.request_timeout) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            self.logger.warning(f"Rate limit hit for {self.source_name} on attempt {attempt + 1}. Retrying...")
                            await asyncio.sleep(2 ** (attempt + 1))
                            continue
                        else:
                            raise APIError(f"{self.source_name.capitalize()} API error {response.status}: {await response.text()}")
            except aiohttp.ClientError as e:
                raise APIError(f"Network error during {self.source_name} search: {e}")
        raise RateLimitError(f"All retry attempts failed for {self.source_name} due to rate limiting.")

    def _load_cookies(self, domain_filter: str) -> Optional[Dict[str, str]]:
        """Загружает cookies из файла Netscape формата, фильтруя их по домену."""
        if not self.cookies_path or not self.cookies_path.exists(): return None
        cookies = {}
        try:
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    parts = line.split('\t')
                    if len(parts) == 7:
                        domain, _, _, _, _, name, value = parts
                        if domain_filter in domain: cookies[name] = value
        except Exception as e:
            self.logger.error(f"Failed to load or parse cookies from {self.cookies_path}: {e}")
            return None
        return cookies

    @abstractmethod
    def _parse_results(self, data: dict, query: str) -> List[VideoMetadata]:
        """Абстрактный метод для парсинга результатов, специфичный для каждой платформы."""
        pass