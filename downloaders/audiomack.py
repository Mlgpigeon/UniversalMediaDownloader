"""
Audiomack downloader using Selenium to intercept streaming URL.
"""
import os
import re
import time
import json
import urllib.request
from typing import Optional

from .base import BaseDownloader, DownloadConfig, DownloadProgress, OutputFormat


class AudiomackDownloader(BaseDownloader):
    """Downloader for Audiomack using browser automation."""
    
    PLATFORM_NAME = "Audiomack"
    SUPPORTED_DOMAINS = ["audiomack.com", "www.audiomack.com"]
    
    def _get_driver(self):
        """Initialize Selenium WebDriver."""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--mute-audio")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    
    def _extract_streaming_url(self, url: str) -> tuple[Optional[str], dict]:
        """Load page and intercept streaming URL from network traffic."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        driver = self._get_driver()
        streaming_url = None
        metadata = {"title": "Unknown", "artist": "Unknown", "id": "unknown"}
        
        try:
            self._report_progress(DownloadProgress(
                percent=10, status="downloading",
                message="Cargando página..."
            ))
            
            driver.get(url)
            time.sleep(3)
            
            # Close cookie banner
            self._report_progress(DownloadProgress(
                percent=15, status="downloading",
                message="Cerrando popups..."
            ))
            
            try:
                cookie_btn = driver.find_element(By.CSS_SELECTOR, "[class*='qc-cmp2'] button[mode='primary']")
                cookie_btn.click()
                time.sleep(1)
            except:
                pass
            
            # Remove overlays
            driver.execute_script("""
                document.querySelectorAll('[class*="qc-cmp2"], [class*="WebToApp"]').forEach(el => el.remove());
            """)
            
            # Extract metadata from URL (most reliable)
            match = re.search(r'audiomack\.com/([^/]+)/song/([^/?]+)', url)
            if match:
                metadata["artist"] = match.group(1).replace('-', ' ').title()
                metadata["title"] = match.group(2).replace('-', ' ').title()
                metadata["id"] = match.group(2)
            
            # Try to get better title from page
            try:
                h1 = driver.find_element(By.TAG_NAME, "h1")
                text = h1.text.strip()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                if len(lines) >= 2:
                    metadata["artist"] = lines[0]
                    metadata["title"] = lines[1]
                elif len(lines) == 1:
                    metadata["title"] = lines[0]
            except:
                pass
            
            # Click play button
            self._report_progress(DownloadProgress(
                percent=25, status="downloading",
                message="Iniciando reproducción..."
            ))
            
            try:
                play_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-amlabs-play-button='true']"))
                )
                driver.execute_script("arguments[0].click();", play_btn)
            except Exception as e:
                raise Exception(f"No se encontró botón de play: {e}")
            
            # Wait for audio to load
            self._report_progress(DownloadProgress(
                percent=35, status="downloading",
                message="Esperando carga de audio..."
            ))
            time.sleep(8)
            
            # Get network logs and find audio URL
            self._report_progress(DownloadProgress(
                percent=50, status="downloading",
                message="Buscando URL de audio..."
            ))
            
            logs = driver.get_log("performance")
            
            for entry in logs:
                try:
                    log = json.loads(entry["message"])["message"]
                    if log["method"] == "Network.requestWillBeSent":
                        req_url = log["params"]["request"]["url"]
                        
                        # Look for music.audiomack.com URLs with audio extensions
                        if "music.audiomack.com" in req_url:
                            streaming_url = req_url
                            break
                except:
                    continue
            
        finally:
            driver.quit()
        
        return streaming_url, metadata
    
    def _download_file(self, url: str, dest_path: str):
        """Download file with progress reporting."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://audiomack.com/",
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=60) as response:
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(dest_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total > 0:
                        pct = 60 + (downloaded / total) * 35
                        self._report_progress(DownloadProgress(
                            percent=pct,
                            status="downloading",
                            message=f"Descargando... {downloaded // 1024} KB / {total // 1024} KB"
                        ))
    
    def download(self, config: DownloadConfig) -> dict:
        """Download from Audiomack."""
        self._report_progress(DownloadProgress(
            status="downloading",
            message="Iniciando descarga de Audiomack..."
        ))
        
        # Get streaming URL
        streaming_url, metadata = self._extract_streaming_url(config.url)
        
        if not streaming_url:
            raise Exception("No se pudo obtener la URL de streaming.")
        
        # Clean metadata
        def clean(text):
            text = text.replace('\n', ' ').replace('\r', ' ')
            text = re.sub(r'[<>:"/\\|?*]', '_', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        metadata["title"] = clean(metadata["title"])[:100]
        metadata["artist"] = clean(metadata["artist"])[:50]
        
        self._report_progress(DownloadProgress(
            percent=55, status="downloading",
            message=f"Descargando: {metadata['title']}"
        ))
        
        # Determine extension
        ext = "m4a" if ".m4a" in streaming_url else "mp3"
        
        filename = f"{metadata['artist']} - {metadata['title']} [{metadata['id']}].{ext}"
        dest_path = os.path.join(config.output_dir, filename)
        
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Download
        self._download_file(streaming_url, dest_path)
        
        # Convert to MP3 if needed
        if config.output_format == OutputFormat.AUDIO and ext == "m4a" and self._has_ffmpeg():
            mp3_path = dest_path.rsplit('.', 1)[0] + '.mp3'
            ffmpeg = self._get_ffmpeg_path()
            
            self._report_progress(DownloadProgress(
                percent=96, status="processing",
                message="Convirtiendo a MP3..."
            ))
            
            import subprocess
            subprocess.run([
                ffmpeg, "-i", dest_path,
                "-acodec", "libmp3lame", "-q:a", "2",
                mp3_path, "-y"
            ], capture_output=True)
            
            if os.path.exists(mp3_path):
                os.remove(dest_path)
                dest_path = mp3_path
        
        self._report_progress(DownloadProgress(
            percent=100, status="finished",
            message=f"Descarga completa: {metadata['title']}"
        ))
        
        return {
            "title": metadata["title"],
            "artist": metadata["artist"],
            "id": metadata["id"],
            "filepath": dest_path,
        }
    
    def _get_platform_options(self, config: DownloadConfig) -> dict:
        """Not used - we override download() directly."""
        return {}