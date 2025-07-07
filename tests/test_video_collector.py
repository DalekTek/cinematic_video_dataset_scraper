# tests/test_video_collector.py
import pytest
from unittest.mock import patch, AsyncMock, ANY

from src.video_collector import VideoCollector
from src.interfaces import VideoMetadata
from src.exceptions import DownloadError, ValidationError

@pytest.fixture
def video_collector(mock_config) -> VideoCollector:
    """
    Фикстура для создания экземпляра VideoCollector с моками.
    """
    with patch('src.video_collector.VideoSearcher'), \
         patch('src.video_collector.VideoDownloader'), \
         patch('src.video_collector.VideoProcessor'), \
         patch('src.video_collector.VideoValidator'):
        collector = VideoCollector(mock_config)
        return collector

@pytest.mark.asyncio
async def test_collect_videos_happy_path(video_collector: VideoCollector, sample_video_metadata: VideoMetadata):
    """
    Тестирует успешный сценарий сбора видео.
    """
    # Настраиваем моки
    video_collector.searcher.search_videos = AsyncMock(return_value=[sample_video_metadata])
    
    # Мокируем _process_single_video, чтобы он возвращал успешный результат
    processed_meta = sample_video_metadata
    processed_meta.file_path = "path/to/final.mp4"
    processed_meta.hash_value = "final_hash"
    
    with patch.object(video_collector, '_process_single_video', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = processed_meta
        
        # Запускаем тест
        keywords = ["neon"]
        result = await video_collector.collect_videos(keywords)

        # Проверки
        video_collector.searcher.search_videos.assert_called_once_with(keywords[0], ANY)
        mock_process.assert_called_once_with(sample_video_metadata)
        assert len(result) == 1
        assert result[0].hash_value == "final_hash"

@pytest.mark.asyncio
@pytest.mark.parametrize("exception_to_raise", [
    DownloadError("Download failed"),
    ValidationError("Validation failed"),
    Exception("Generic error")
])
async def test_process_single_video_handles_errors(video_collector: VideoCollector, sample_video_metadata: VideoMetadata, exception_to_raise):
    """
    Тестирует, что ошибки при обработке одного видео корректно обрабатываются.
    """
    # Настраиваем мок, чтобы он вызывал исключение
    video_collector.downloader.download_video = AsyncMock(side_effect=exception_to_raise)

    result = await video_collector._process_single_video(sample_video_metadata)

    # Проверяем, что в случае любой ошибки метод возвращает None
    assert result is None
    # Проверяем, что временный файл был удален (мокаем unlink)
    with patch('pathlib.Path.unlink') as mock_unlink:
        await video_collector._process_single_video(sample_video_metadata)
        mock_unlink.assert_called_with(missing_ok=True)