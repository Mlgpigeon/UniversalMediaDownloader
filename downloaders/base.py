"""
Base downloader class with common functionality.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional
import os
import shutil

from yt_dlp import YoutubeDL


class OutputFormat(Enum):
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class DownloadProgress:
    """Progress information for downloads."""
    percent: float = 0.0
    speed: str = ""
    eta: str = ""
    status: str = "idle"  # idle, downloading, processing, finished, error
    message: str = ""


@dataclass
class DownloadConfig:
    """Configuration for a download."""
    url: str
    output_dir: str
    output_format: OutputFormat = OutputFormat.VIDEO
    cookies_file: Optional[str] = None
    ffmpeg_path: Optional[str] = None


class BaseDownloader(ABC):
    """Abstract base class for media downloaders."""
    
    PLATFORM_NAME: str = "Unknown"
    SUPPORTED_DOMAINS: list[str] = []
    
    def __init__(self, progress_callback: Optional[Callable[[DownloadProgress], None]] = None):
        self.progress_callback = progress_callback
        self._ffmpeg_path: Optional[str] = None
    
    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if this downloader can handle the given URL."""
        url_lower = url.lower()
        return any(domain in url_lower for domain in cls.SUPPORTED_DOMAINS)
    
    def _report_progress(self, progress: DownloadProgress):
        """Report progress to the callback if set."""
        if self.progress_callback:
            self.progress_callback(progress)
    
    def _get_ffmpeg_path(self) -> Optional[str]:
        """Get FFmpeg path, trying imageio-ffmpeg first, then system."""
        if self._ffmpeg_path:
            return self._ffmpeg_path
            
        # Try imageio-ffmpeg first
        try:
            import imageio_ffmpeg
            self._ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            return self._ffmpeg_path
        except Exception:
            pass
        
        # Fallback to system ffmpeg
        if shutil.which("ffmpeg"):
            self._ffmpeg_path = shutil.which("ffmpeg")
            return self._ffmpeg_path
        
        return None
    
    def _has_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        return self._get_ffmpeg_path() is not None
    
    def _create_progress_hook(self) -> Callable:
        """Create a yt-dlp progress hook."""
        def hook(d: dict):
            status = d.get("status", "")
            
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                percent = (downloaded * 100 / total) if total > 0 else 0
                
                speed = d.get("_speed_str", "").strip()
                eta = d.get("_eta_str", "").strip()
                
                self._report_progress(DownloadProgress(
                    percent=percent,
                    speed=speed,
                    eta=eta,
                    status="downloading",
                    message=f"Descargando… {percent:.1f}%"
                ))
                
            elif status == "finished":
                self._report_progress(DownloadProgress(
                    percent=95,
                    status="processing",
                    message="Procesando archivo…"
                ))
                
            elif status == "error":
                self._report_progress(DownloadProgress(
                    status="error",
                    message="Error en la descarga"
                ))
        
        return hook
    
    def _create_postprocessor_hook(self) -> Callable:
        """Create a yt-dlp postprocessor hook."""
        def hook(d: dict):
            status = d.get("status", "")
            
            if status == "started":
                pp = d.get("postprocessor", "")
                if "ExtractAudio" in pp:
                    msg = "Extrayendo audio…"
                elif "Metadata" in pp:
                    msg = "Añadiendo metadatos…"
                else:
                    msg = "Procesando…"
                    
                self._report_progress(DownloadProgress(
                    percent=97,
                    status="processing",
                    message=msg
                ))
                
            elif status == "finished":
                self._report_progress(DownloadProgress(
                    percent=99,
                    status="processing",
                    message="Finalizando…"
                ))
        
        return hook
    
    def _get_base_options(self, config: DownloadConfig) -> dict:
        """Get base yt-dlp options common to all downloaders."""
        os.makedirs(config.output_dir, exist_ok=True)
        
        opts = {
            "outtmpl": os.path.join(config.output_dir, "%(title).120s [%(id)s].%(ext)s"),
            "noplaylist": True,
            "retries": 10,
            "fragment_retries": 10,
            "concurrent_fragment_downloads": 4,
            "progress_hooks": [self._create_progress_hook()],
            "postprocessor_hooks": [self._create_postprocessor_hook()],
            "quiet": True,
            "no_warnings": True,
        }
        
        # Add ffmpeg path if available
        ffmpeg = config.ffmpeg_path or self._get_ffmpeg_path()
        if ffmpeg:
            opts["ffmpeg_location"] = ffmpeg
        
        # Add cookies if provided
        if config.cookies_file:
            opts["cookiefile"] = config.cookies_file
        
        return opts
    
    @abstractmethod
    def _get_platform_options(self, config: DownloadConfig) -> dict:
        """Get platform-specific yt-dlp options. Override in subclasses."""
        pass
    
    def download(self, config: DownloadConfig) -> dict:
        """
        Download media from URL.
        
        Returns:
            dict: Info dict from yt-dlp with download results.
            
        Raises:
            Exception: If download fails.
        """
        self._report_progress(DownloadProgress(
            status="downloading",
            message="Iniciando descarga…"
        ))
        
        # Merge base and platform-specific options
        opts = self._get_base_options(config)
        opts.update(self._get_platform_options(config))
        
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(config.url, download=True)
                
                self._report_progress(DownloadProgress(
                    percent=100,
                    status="finished",
                    message=f"Descarga completa: {info.get('title', 'archivo')}"
                ))
                
                return info
                
        except Exception as e:
            self._report_progress(DownloadProgress(
                status="error",
                message=f"Error: {str(e)}"
            ))
            raise
