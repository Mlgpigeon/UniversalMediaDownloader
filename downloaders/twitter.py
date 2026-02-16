"""
X (Twitter) downloader implementation.
"""
from .base import BaseDownloader, DownloadConfig, OutputFormat


class TwitterDownloader(BaseDownloader):
    """Downloader for X (Twitter) videos."""
    
    PLATFORM_NAME = "X (Twitter)"
    SUPPORTED_DOMAINS = [
        "twitter.com",
        "x.com",
        "mobile.twitter.com",
        "mobile.x.com",
    ]
    
    def _get_platform_options(self, config: DownloadConfig) -> dict:
        """Get Twitter/X-specific options."""
        opts = {}
        
        if config.output_format == OutputFormat.AUDIO:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
            ]
        else:
            # Video format
            if self._has_ffmpeg():
                opts["format"] = "bestvideo+bestaudio/best"
                opts["merge_output_format"] = "mp4"
            else:
                opts["format"] = "best"
        
        return opts
