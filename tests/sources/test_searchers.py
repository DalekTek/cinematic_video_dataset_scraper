# tests/sources/test_searchers.py
import pytest
from aioresponses import aioresponses

from src.config import Config
from src.sources.youtube_searcher import YouTubeSearcher
from src.sources.vimeo_searcher import VimeoSearcher
from src.interfaces import VideoMetadata

@pytest.mark.asyncio
async def test_vimeo_searcher_success(mock_config: Config):
    """
    Тестирует успешный поиск в VimeoSearcher.
    """
    searcher = VimeoSearcher(mock_config)
    query = "cinematic explosion"
    
    mock_response = {
        "items": [
            {"title": "Vimeo Boom", "url": "http://vimeo.com/1", "duration": 120},
            {"title": "Another Boom", "url": "http://vimeo.com/2", "duration": 45}
        ]
    }
    
    with aioresponses() as m:
        m.get(searcher.API_URL, payload=mock_response, status=200)
        results = await searcher.search_videos(query, 2)

    assert len(results) == 2
    assert isinstance(results[0], VideoMetadata)
    assert results[0].source == "vimeo"
    assert results[0].category == "explosions"
    assert results[1].url == "http://vimeo.com/2"

@pytest.mark.asyncio
async def test_vimeo_searcher_api_error(mock_config: Config, caplog):
    """
    Тестирует обработку ошибки API в VimeoSearcher.
    """
    searcher = VimeoSearcher(mock_config)
    
    with aioresponses() as m:
        m.get(searcher.API_URL, status=403, body="Forbidden")
        results = await searcher.search_videos("test", 1)

    assert len(results) == 0
    assert "Vimeo API error 403: Forbidden" in caplog.text

@pytest.mark.asyncio
@pytest.mark.parametrize("query, expected_category", [
    ("neon cyberpunk", "neon"),
    ("slow motion blast", "explosions"),
    ("dramatic smoke effect", "smoke"),
    ("camera spin shot", "camera-move"),
    ("face morphing effect", "transformations"),
    ("epic fight scene", "action-scenes")
])
def test_categorize_video(mock_config: Config, query: str, expected_category: str):
    """
    Тестирует логику категоризации в базовом поисковике.
    """
    # Используем любой поисковик, т.к. логика в BaseSearcher
    searcher = VimeoSearcher(mock_config)
    category = searcher._categorize_video(query)
    assert category == expected_category