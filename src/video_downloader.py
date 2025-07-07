import asyncio
import logging
from pathlib import Path
from typing import Optional

from .interfaces import IVideoDownloader
from .config import Config
from .exceptions import DownloadError


class VideoDownloader(IVideoDownloader):
    """
    Класс для скачивания видео с использованием yt-dlp.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def download_video(self, url: str, output_path: str, cookies_file: Optional[Path]) -> bool:
        """
        Асинхронно скачивает видео по URL.
        """
        self.logger.debug(f"Attempting to download from: {url}")

        cmd = [
            'yt-dlp',
            '--format', 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
            '--output', output_path,
            '--no-playlist',
            '--limit-rate', '10M',
            '--force-ipv4',
            '--no-check-certificate',
            '--retries', str(self.config.retry_attempts),
            '--socket-timeout', str(self.config.request_timeout),
            '--quiet'  # Уменьшаем количество логов от yt-dlp
        ]

        if cookies_file and cookies_file.exists() and cookies_file.stat().st_size > 0:
            cmd.extend(['--cookies', str(cookies_file)])
            self.logger.debug(f"Using cookies: {cookies_file.name}")

        cmd.append(url)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            timeout = (self.config.request_timeout + 5) * self.config.retry_attempts
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            if process.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                self.logger.info(f"Successfully downloaded: {url}")
                return True
            else:
                error_message = stderr.decode('utf-8', errors='ignore').strip()
                raise DownloadError(f"yt-dlp failed for {url}. Code: {process.returncode}. Error: {error_message}")

        except asyncio.TimeoutError:
            raise DownloadError(f"Download timed out for: {url}")
        except Exception as e:
            # Перехватываем либо наше исключение, либо новое
            if not isinstance(e, DownloadError):
                raise DownloadError(f"Unexpected download error for {url}: {e}")
            raise e
        finally:
            # Убеждаемся, что недокачанный файл удален
            output_p = Path(output_path)
            if output_p.exists() and output_p.stat().st_size == 0:
                output_p.unlink(missing_ok=True)