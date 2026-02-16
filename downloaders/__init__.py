"""
Downloaders module - handles media downloads from various platforms.
"""
from .base import (
    BaseDownloader,
    DownloadConfig,
    DownloadProgress,
    OutputFormat,
)
from .manager import DownloadManager, DOWNLOADERS
from .youtube import YouTubeDownloader
from .twitter import TwitterDownloader
from .instagram import InstagramDownloader


__all__ = [
    # Core classes
    "BaseDownloader",
    "DownloadConfig",
    "DownloadProgress",
    "OutputFormat",
    # Manager
    "DownloadManager",
    "DOWNLOADERS",
    # Platform-specific
    "YouTubeDownloader",
    "TwitterDownloader",
    "InstagramDownloader",
    "AudiomackDownloader",
]
