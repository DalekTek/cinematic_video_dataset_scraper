import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.config import Config
from src.video_collector import VideoCollector
from src.dataset_builder import DatasetBuilder
from src.logger import setup_logging
from src.exceptions import ConfigError

async def main() -> None:
    """
    Главная функция для запуска сбора датасета.
    """
    # Загрузка переменных окружения из .env файла
    env_path = Path('.') / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        print("Warning: .env file not found. Please create it from .env.example.")

    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Загрузка конфигурации
        config = Config()

        # Создание основных компонентов системы
        video_collector = VideoCollector(config)
        dataset_builder = DatasetBuilder(config)

        # Список ключевых слов для поиска кинематографичных видео
        keywords = [
            "neon lights cinematic", "explosion slow motion", "camera spin movement",
            "bullet time effect", "smoke dramatic lighting", "cinematic action scene",
            "dramatic camera angle", "neon cyberpunk aesthetic", "slow motion destruction",
            "cinematic transformation"
        ]

        logger.info("Starting cinematic video dataset collection")
        logger.info(f"Target videos count: {config.target_videos_count}")
        logger.info(f"Sources enabled: {', '.join(config.sources)}")

        # Сбор видеофрагментов
        collected_videos = await video_collector.collect_videos(keywords)

        if not collected_videos:
            logger.warning("No videos were collected. Please check your keywords, API keys, and cookies.")
            return

        # Построение датасета
        dataset_path = await dataset_builder.build_dataset(collected_videos)

        logger.info(f"Dataset successfully created at: {dataset_path}")
        logger.info("Process completed successfully")

    except ConfigError as e:
        logger.critical(f"Configuration error: {e}. Please check your .env file and configuration.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"A critical error occurred during execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Для Windows может потребоваться следующая политика для asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())