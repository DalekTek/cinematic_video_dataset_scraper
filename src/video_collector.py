import asyncio
import logging
import hashlib
from typing import List, Optional
from dataclasses import replace
import re
import random

from .interfaces import VideoMetadata
from .config import Config
from .video_searcher import VideoSearcher
from .video_downloader import VideoDownloader
from .video_processor import VideoProcessor
from .video_validator import VideoValidator
from .exceptions import DownloadError, ProcessingError, ValidationError


class VideoCollector:
    """
    Основной класс-координатор для сбора, обработки и валидации видео.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.searcher = VideoSearcher(config)
        self.downloader = VideoDownloader(config)
        self.processor = VideoProcessor(config)
        self.validator = VideoValidator(config)
        self.download_semaphore = asyncio.Semaphore(config.max_concurrent_downloads)

    async def collect_videos(self, keywords: List[str]) -> List[VideoMetadata]:
        """
        Организует полный цикл сбора видео по списку ключевых слов.
        Стратегия изменена на последовательный обход ключевых слов, чтобы избежать rate-лимитов.
        """
        self.logger.info(f"Starting video collection for {len(keywords)} keywords.")

        all_found_videos = []
        # Рассчитываем, сколько примерно видео нужно искать на каждое ключевое слово, с запасом 150%
        limit_per_keyword = int((self.config.target_videos_count / len(keywords)) * 1.5)
        if limit_per_keyword < 1:
            limit_per_keyword = 1

        # Последовательно проходим по ключевым словам
        for keyword in keywords:
            self.logger.info(f"Searching for keyword: '{keyword}'")
            # Поиск по всем источникам для ОДНОГО ключевого слова
            found_for_keyword = await self.searcher.search_videos(keyword, limit_per_keyword)
            all_found_videos.extend(found_for_keyword)

            # Добавляем задержку между запросами по разным ключевым словам
            delay = random.uniform(1.0, 3.0)
            self.logger.debug(f"Waiting for {delay:.2f} seconds before next keyword.")
            await asyncio.sleep(delay)

        random.shuffle(all_found_videos)
        self.logger.info(f"Found a total of {len(all_found_videos)} potential videos. Starting processing.")

        # Далее логика обработки остается прежней, но теперь она работает с более реалистичным списком
        collected_videos: List[VideoMetadata] = []

        if not all_found_videos:
            return []

        # Создаем задачи на обработку, но не больше чем нужно с запасом
        tasks_to_run = min(len(all_found_videos), self.config.target_videos_count * 2)
        process_tasks = [
            asyncio.create_task(self._process_single_video(video_meta))
            for video_meta in all_found_videos[:tasks_to_run]
        ]

        for future in asyncio.as_completed(process_tasks):
            try:
                result = await future
                if isinstance(result, VideoMetadata):
                    collected_videos.append(result)
                    self.logger.info(
                        f"Progress: {len(collected_videos)} / {self.config.target_videos_count} videos collected.")
                    if len(collected_videos) >= self.config.target_videos_count:
                        # Если набрали нужное количество, отменяем оставшиеся задачи
                        for task in process_tasks:
                            if not task.done():
                                task.cancel()
                        break
            except asyncio.CancelledError:
                self.logger.info("Task was cancelled as target video count reached.")
            except Exception as e:
                self.logger.error(f"A video processing task failed in main loop: {e}", exc_info=True)

        self.logger.info(f"Successfully collected and processed {len(collected_videos)} videos.")
        return collected_videos[:self.config.target_videos_count]

    async def _process_single_video(self, video_metadata: VideoMetadata) -> Optional[VideoMetadata]:
        """
        Полный конвейер обработки для одного видео: скачивание, валидация, обработка, финальная валидация.
        """
        async with self.download_semaphore:
            await asyncio.sleep(random.uniform(0.5, 2.0))  # Случайная задержка

            video_hash = hashlib.sha1(video_metadata.url.encode()).hexdigest()[:10]
            temp_file = self.config.temp_dir / f"temp_{video_hash}.mp4"

            try:
                # 1. Скачивание
                await self.downloader.download_video(video_metadata.url, str(temp_file), video_metadata.cookies_file)

                # 2. Предварительная валидация (длительность, водяные знаки)
                await self.validator.validate_video(str(temp_file))

                # 3. Обработка (обрезка)
                category_dir = self.config.base_output_dir / video_metadata.category
                safe_filename = self._sanitize_filename(video_metadata.title)
                final_filename = f"{safe_filename}_{video_hash}.mp4"
                final_file = category_dir / final_filename

                await self.processor.process_video(str(temp_file), str(final_file))

                # 4. Финальная валидация (проверка на дубликат по хешу)
                final_file_hash = await self.validator.calculate_file_hash(str(final_file))
                if await self.validator.check_for_duplicate(final_file_hash):
                    raise ValidationError(f"Duplicate content detected for final file: {final_file}")

                return replace(
                    video_metadata, file_path=str(final_file), hash_value=final_file_hash
                )

            except (DownloadError, ProcessingError, ValidationError) as e:
                self.logger.warning(f"Failed to process video {video_metadata.url}: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error processing {video_metadata.url}: {e}", exc_info=True)
                return None
            finally:
                temp_file.unlink(missing_ok=True)

    def _sanitize_filename(self, text: str) -> str:
        """
        Очищает строку, чтобы она стала безопасным именем файла для Windows.
        """
        sanitized = re.sub(r'[\\/*?:"<>|]', "", text)
        sanitized = re.sub(r'\s+', '_', sanitized).strip('_')
        return sanitized[:100]