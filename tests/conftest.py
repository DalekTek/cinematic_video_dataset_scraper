# tests/conftest.py
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.config import Config
from src.interfaces import VideoMetadata


@pytest.fixture(scope="session")
def test_output_dir(tmp_path_factory):
    """
    Создает временную директорию для тестовых артефактов.
    """
    return tmp_path_factory.mktemp("output")


@pytest.fixture
def mock_config(test_output_dir, monkeypatch) -> Config:
    """
    Фикстура для создания мок-объекта Config.
    """
    # Мокаем os.getenv, чтобы не зависеть от реального .env файла
    monkeypatch.setenv("RAPIDAPI_KEY", "test_api_key")
    monkeypatch.setenv("TARGET_VIDEOS_COUNT", "10")

    # Создаем мок-объект Config, но с реальными путями во временной директории
    with patch('src.config.Config._create_directories'), \
            patch('src.config.Config._validate_cookies'):
        config = Config()

    config.base_output_dir = test_output_dir / "dataset"
    config.temp_dir = test_output_dir / "temp"
    config.cookies_dir = test_output_dir / "cookies"

    # Создаем директории вручную для теста
    config.base_output_dir.mkdir(exist_ok=True)
    config.temp_dir.mkdir(exist_ok=True)
    config.cookies_dir.mkdir(exist_ok=True)

    for category in config.video_categories:
        (config.base_output_dir / category).mkdir(exist_ok=True)

    return config


@pytest.fixture
def sample_video_metadata() -> VideoMetadata:
    """
    Фикстура, предоставляющая тестовый объект VideoMetadata.
    """
    return VideoMetadata(
        title="Test Neon Video",
        url="https://youtube.com/watch?v=test",
        duration=10.0,
        source="youtube",
        category="neon",
        cookies_file=Path("cookies/youtube-cookies.txt")
    )