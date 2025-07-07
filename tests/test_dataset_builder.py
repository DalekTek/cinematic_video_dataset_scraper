import pytest
import pandas as pd
import json
from pathlib import Path

from src.dataset_builder import DatasetBuilder
from src.interfaces import VideoMetadata


@pytest.fixture
def dataset_builder(mock_config) -> DatasetBuilder:
    """
    Фикстура для создания экземпляра DatasetBuilder.
    """
    return DatasetBuilder(mock_config)


@pytest.fixture
def processed_videos(mock_config) -> list[VideoMetadata]:
    """
    Фикстура для создания списка обработанных видео для тестов.
    """
    videos = []
    for i in range(3):
        category = "neon" if i % 2 == 0 else "explosions"
        source = "youtube" if i % 2 == 0 else "vimeo"

        # Создаем фейковые видеофайлы
        video_dir = mock_config.base_output_dir / category
        video_dir.mkdir(exist_ok=True)
        file_path = video_dir / f"video_{i}.mp4"
        file_path.touch()

        videos.append(VideoMetadata(
            title=f"Video {i}",
            url=f"http://example.com/{i}",
            duration=float(i + 2),
            source=source,
            category=category,
            file_path=str(file_path),
            hash_value=f"hash_{i}"
        ))
    return videos


@pytest.mark.asyncio
async def test_build_dataset(dataset_builder: DatasetBuilder, processed_videos: list[VideoMetadata]):
    """
    Тестирует полный цикл работы DatasetBuilder.
    """
    archive_path_str = await dataset_builder.build_dataset(processed_videos)
    archive_path = Path(archive_path_str)

    # Проверяем, что архив создан
    assert archive_path.exists()
    assert archive_path.name == "cinematic_dataset.zip"

    # Проверяем, что индексные файлы созданы в директории датасета
    base_dir = dataset_builder.config.base_output_dir
    assert (base_dir / "dataset_index.csv").exists()
    assert (base_dir / "dataset_index.json").exists()
    assert (base_dir / "dataset_stats.json").exists()


@pytest.mark.asyncio
async def test_save_index(dataset_builder: DatasetBuilder, processed_videos: list[VideoMetadata]):
    """
    Тестирует сохранение индексных файлов.
    """
    index_data = dataset_builder._create_index(processed_videos)
    await dataset_builder._save_index(index_data)

    # Проверка CSV
    csv_path = dataset_builder.config.base_output_dir / "dataset_index.csv"
    df = pd.read_csv(csv_path)
    assert len(df) == len(processed_videos)
    assert df.iloc[0]['title'] == "Video 0"

    # Проверка JSON
    json_path = dataset_builder.config.base_output_dir / "dataset_index.json"
    with open(json_path, 'r') as f:
        data = json.load(f)
    assert len(data) == len(processed_videos)
    assert data[1]['source'] == "vimeo"


@pytest.mark.asyncio
async def test_generate_statistics(dataset_builder: DatasetBuilder, processed_videos: list[VideoMetadata]):
    """
    Тестирует генерацию файла статистики.
    """
    await dataset_builder._generate_statistics(processed_videos)
    stats_path = dataset_builder.config.base_output_dir / "dataset_stats.json"

    with open(stats_path, 'r') as f:
        stats = json.load(f)

    assert stats['total_videos'] == 3
    assert stats['categories']['neon'] == 2
    assert stats['categories']['explosions'] == 1
    assert stats['sources']['youtube'] == 2
    assert stats['total_duration_sec'] == 2.0 + 3.0 + 4.0