import asyncio
import json
import logging
import zipfile
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

from .interfaces import VideoMetadata
from .config import Config


class DatasetBuilder:
    """
    Класс для построения финального датасета: создание индексов, статистики и архива.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def build_dataset(self, videos: List[VideoMetadata]) -> str:
        """
        Запускает процесс построения финального датасета.
        """
        self.logger.info(f"Starting dataset build with {len(videos)} videos.")

        index_data = self._create_index(videos)
        await self._save_index(index_data)
        await self._generate_statistics(videos)

        archive_path = await self._create_archive(videos)

        self.logger.info(f"Dataset build complete. Archive created at: {archive_path}")
        return archive_path

    def _create_index(self, videos: List[VideoMetadata]) -> List[Dict[str, Any]]:
        """
        Создает индексные данные из списка метаданных видео.
        """
        return [{
            'id': i,
            'title': video.title,
            'url': video.url,
            'duration': video.duration,
            'source': video.source,
            'category': video.category,
            'file_path': str(Path(video.file_path).relative_to(self.config.base_output_dir.parent)),
            'hash_value': video.hash_value
        } for i, video in enumerate(videos)]

    async def _save_index(self, index_data: List[Dict[str, Any]]) -> None:
        """
        Сохраняет индексные данные в форматах CSV и JSON.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._sync_save_index, index_data)

    def _sync_save_index(self, index_data: List[Dict[str, Any]]):
        """Синхронная часть сохранения индексов."""
        df = pd.DataFrame(index_data)
        csv_path = self.config.base_output_dir / "dataset_index.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')

        json_path = self.config.base_output_dir / "dataset_index.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Index files saved to {csv_path} and {json_path}")

    async def _generate_statistics(self, videos: List[VideoMetadata]) -> None:
        """
        Генерирует и сохраняет файл со статистикой по датасету.
        """
        stats = {
            'total_videos': len(videos),
            'categories': {},
            'sources': {},
            'total_duration_sec': 0,
            'average_duration_sec': 0
        }

        for video in videos:
            stats['categories'][video.category] = stats['categories'].get(video.category, 0) + 1
            stats['sources'][video.source] = stats['sources'].get(video.source, 0) + 1
            stats['total_duration_sec'] += video.duration

        if len(videos) > 0:
            stats['average_duration_sec'] = round(stats['total_duration_sec'] / len(videos), 2)

        stats_path = self.config.base_output_dir / "dataset_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Statistics generated at: {stats_path}")

    async def _create_archive(self, videos: List[VideoMetadata]) -> str:
        """
        Создает ZIP-архив с видеофайлами и метаданными.
        """
        loop = asyncio.get_running_loop()
        archive_path = self.config.base_output_dir.parent / "cinematic_dataset.zip"
        await loop.run_in_executor(None, self._sync_create_archive, videos, archive_path)
        return str(archive_path)

    def _sync_create_archive(self, videos: List[VideoMetadata], archive_path: Path):
        """Синхронная часть создания архива."""
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for video in videos:
                file_path = Path(video.file_path)
                if file_path.exists():
                    arcname = file_path.relative_to(self.config.base_output_dir.parent)
                    zipf.write(file_path, arcname)

            for index_file in ["dataset_index.csv", "dataset_index.json", "dataset_stats.json"]:
                file_path = self.config.base_output_dir / index_file
                if file_path.exists():
                    arcname = file_path.relative_to(self.config.base_output_dir.parent)
                    zipf.write(file_path, arcname)

        self.logger.info(f"Archive created: {archive_path}")