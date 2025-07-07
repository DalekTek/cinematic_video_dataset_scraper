import hashlib
import logging
from pathlib import Path
from typing import Set, List
import asyncio
import cv2
import numpy as np

from .interfaces import IVideoValidator
from .config import Config
from .video_processor import VideoProcessor
from .exceptions import ValidationError


class VideoValidator(IVideoValidator):
    """
    Класс для всесторонней валидации видеофайлов.
    """
    WATERMARK_MATCH_THRESHOLD = 0.8
    NUM_FRAMES_TO_CHECK = 5

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processor = VideoProcessor(config)
        self.seen_hashes: Set[str] = set()
        self.watermark_templates = self._load_watermark_templates()

    def _load_watermark_templates(self) -> List[np.ndarray]:
        """
        Загружает шаблоны водяных знаков из директории 'resources/watermarks'.
        """
        templates_dir = Path("resources/watermarks")
        templates = []
        if not templates_dir.exists():
            self.logger.warning(
                f"Watermark templates directory not found: {templates_dir}. Skipping watermark detection.")
            return templates

        for template_path in templates_dir.glob("*.png"):
            template = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
            if template is not None:
                templates.append(template)
                self.logger.info(f"Loaded watermark template: {template_path.name}")
        return templates

    async def validate_video(self, video_path: str) -> bool:
        """
        Выполняет полную валидацию видеофайла.
        """
        # 1. Проверка существования файла
        if not Path(video_path).exists():
            raise ValidationError(f"Video file not found: {video_path}")

        # 2. Проверка длительности
        duration = await self.processor.get_video_duration(video_path)
        if duration is None:
            raise ValidationError(f"Could not get duration for: {video_path}")
        if duration < self.config.min_video_duration:
            raise ValidationError(f"Video too short ({duration:.2f}s): {video_path}")

        # 3. Проверка на водяные знаки
        if self.watermark_templates:
            has_watermark = await self._has_watermark(video_path)
            if has_watermark:
                raise ValidationError(f"Watermark detected in: {video_path}")

        # 4. Проверка на дубликаты (выполняется для финального файла в VideoCollector)
        # Здесь мы не проверяем, так как этот метод вызывается для временного файла.
        # Хеш будет вычислен для финального, обработанного файла.

        self.logger.info(f"Video validation passed for: {video_path}")
        return True

    async def check_for_duplicate(self, file_hash: str) -> bool:
        """
        Проверяет, является ли хеш дубликатом, и добавляет его в набор.
        """
        if file_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(file_hash)
        return False

    async def calculate_file_hash(self, file_path: str) -> str:
        """
        Асинхронно вычисляет SHA-256 хеш файла.
        """
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except IOError as e:
            self.logger.error(f"Could not read file for hashing: {file_path}. Error: {e}")
            raise ValidationError(f"Hashing failed for {file_path}")

    async def _has_watermark(self, video_path: str) -> bool:
        """
        Асинхронная обертка для проверки на водяные знаки.
        """
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                None, self._sync_check_video_for_watermarks, video_path
            )
        except Exception as e:
            self.logger.error(f"Error during watermark detection for {video_path}: {e}")
            return False

    def _sync_check_video_for_watermarks(self, video_path: str) -> bool:
        """
        Синхронная функция, выполняющая проверку видео на наличие водяных знаков.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.logger.error(f"Could not open video file for watermark check: {video_path}")
            return False

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames < 1: return False

            frame_indices = np.linspace(0, total_frames - 1, self.NUM_FRAMES_TO_CHECK, dtype=int)

            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret: continue

                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                for template in self.watermark_templates:
                    if template.shape[0] > gray_frame.shape[0] or template.shape[1] > gray_frame.shape[1]:
                        continue

                    result = cv2.matchTemplate(gray_frame, template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(result)

                    if max_val > self.WATERMARK_MATCH_THRESHOLD:
                        self.logger.debug(
                            f"Watermark match found on frame {idx} with confidence {max_val:.2f} in {video_path}")
                        return True
        finally:
            cap.release()
        return False