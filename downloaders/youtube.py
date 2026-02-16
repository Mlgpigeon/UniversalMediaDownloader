"""
YouTube downloader implementation.
"""
from .base import BaseDownloader, DownloadConfig, OutputFormat


class YouTubeDownloader(BaseDownloader):
    """Downloader for YouTube videos."""
    
    PLATFORM_NAME = "YouTube"
    SUPPORTED_DOMAINS = [
        "youtube.com",
        "youtu.be",
        "youtube-nocookie.com",
        "music.youtube.com",
    ]
    
    def _get_platform_options(self, config: DownloadConfig) -> dict:
        """Get YouTube-specific options."""
        opts = {
            "age_limit": 0,
            "nocheckcertificate": True,
        }
        
        if config.output_format == OutputFormat.AUDIO:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {"key": "FFmpegMetadata"},
            ]
        else:
            # Video format
            if self._has_ffmpeg():
                opts["format"] = "bestvideo+bestaudio/best"
                opts["merge_output_format"] = "mp4"
            else:
                opts["format"] = "best"
        
        return opts
