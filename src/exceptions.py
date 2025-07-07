# src/exceptions.py

class BaseCollectorException(Exception):
    """Базовое исключение для всех ошибок в проекте."""
    pass

class ConfigError(BaseCollectorException):
    """Ошибка, связанная с конфигурацией."""
    pass

class APIError(BaseCollectorException):
    """Ошибка при работе с внешним API."""
    pass

class RateLimitError(APIError):
    """Ошибка, возникающая при превышении лимита запросов к API (HTTP 429)."""
    pass

class DownloadError(BaseCollectorException):
    """Ошибка при скачивании видео."""
    pass

class ProcessingError(BaseCollectorException):
    """Ошибка при обработке видео (например, через FFmpeg)."""
    pass

class ValidationError(BaseCollectorException):
    """Ошибка, когда видео не проходит валидацию."""
    pass