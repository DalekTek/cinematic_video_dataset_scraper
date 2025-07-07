# src/video_processor.py
import asyncio
import logging
import json
from typing import Optional

from .interfaces import IVideoProcessor
from .config import Config
from .exceptions import ProcessingError


class VideoProcessor(IVideoProcessor):
    """
    Класс для обработки видеофайлов с использованием FFmpeg.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def process_video(self, input_path: str, output_path: str) -> bool:
        """
        Обрезает видео до максимальной длительности, указанной в конфиге.
        """
        self.logger.debug(f"Processing video: {input_path} -> {output_path}")
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-t', str(self.config.max_video_duration),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',  # Для веб-оптимизации
            output_path
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.config.request_timeout)

            if process.returncode == 0:
                self.logger.info(f"Successfully processed video: {output_path}")
                return True
            else:
                raise ProcessingError(f"FFmpeg failed for {input_path}: {stderr.decode()}")
        except asyncio.TimeoutError:
            raise ProcessingError(f"Processing timed out for: {input_path}")
        except Exception as e:
            if not isinstance(e, ProcessingError):
                raise ProcessingError(f"Unexpected processing error for {input_path}: {e}")
            raise e

    async def get_video_duration(self, video_path: str) -> Optional[float]:
        """
        Получает длительность видео с помощью ffprobe.
        """
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                data = json.loads(stdout.decode())
                # Ищем длительность в 'format' или в видеопотоке
                duration = data.get('format', {}).get('duration')
                if duration is None:
                    video_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
                    if video_streams:
                        duration = video_streams[0].get('duration')

                if duration:
                    return float(duration)
                else:
                    self.logger.warning(f"Could not find duration info in ffprobe output for {video_path}")
                    return None
            else:
                self.logger.error(f"ffprobe failed for {video_path}: {stderr.decode()}")
                return None
        except Exception as e:
            self.logger.error(f"Duration check error for {video_path}: {e}")
            return None