"""
Download manager that automatically selects the appropriate downloader.
"""
from typing import Callable, Optional, Type

from .base import BaseDownloader, DownloadConfig, DownloadProgress
from .youtube import YouTubeDownloader
from .twitter import TwitterDownloader
from .instagram import InstagramDownloader
from .audiomack import AudiomackDownloader

# Registry of all available downloaders
DOWNLOADERS: list[Type[BaseDownloader]] = [
    YouTubeDownloader,
    TwitterDownloader,
    InstagramDownloader,
    AudiomackDownloader,
]


class DownloadManager:
    """
    Manages downloads across multiple platforms.
    Automatically selects the appropriate downloader based on URL.
    """
    
    def __init__(self, progress_callback: Optional[Callable[[DownloadProgress], None]] = None):
        self.progress_callback = progress_callback
        self._downloaders: dict[str, BaseDownloader] = {}
    
    def _get_downloader(self, url: str) -> BaseDownloader:
        """Get the appropriate downloader for a URL."""
        for downloader_cls in DOWNLOADERS:
            if downloader_cls.can_handle(url):
                # Cache downloader instances
                key = downloader_cls.PLATFORM_NAME
                if key not in self._downloaders:
                    self._downloaders[key] = downloader_cls(self.progress_callback)
                return self._downloaders[key]
        
        raise ValueError(
            f"URL no soportada. Plataformas disponibles: "
            f"{', '.join(d.PLATFORM_NAME for d in DOWNLOADERS)}"
        )
    
    def detect_platform(self, url: str) -> str:
        """Detect which platform a URL belongs to."""
        for downloader_cls in DOWNLOADERS:
            if downloader_cls.can_handle(url):
                return downloader_cls.PLATFORM_NAME
        return "Desconocida"
    
    def download(self, config: DownloadConfig) -> dict:
        """Download media from URL using the appropriate downloader."""
        downloader = self._get_downloader(config.url)
        return downloader.download(config)
    
    @staticmethod
    def get_supported_platforms() -> list[str]:
        """Get list of supported platform names."""
        return [d.PLATFORM_NAME for d in DOWNLOADERS]
