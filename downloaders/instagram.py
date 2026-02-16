"""
Instagram downloader implementation.
"""
from .base import BaseDownloader, DownloadConfig, OutputFormat


class InstagramDownloader(BaseDownloader):
    """Downloader for Instagram videos and reels."""
    
    PLATFORM_NAME = "Instagram"
    SUPPORTED_DOMAINS = [
        "instagram.com",
        "www.instagram.com",
        "instagr.am",
    ]
    
    def _get_platform_options(self, config: DownloadConfig) -> dict:
        """Get Instagram-specific options."""
        opts = {
            # Instagram may require login for some content
            "extractor_args": {
                "instagram": {
                    # Try to get best quality
                    "skip": ["dash"],
                }
            },
        }
        
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
