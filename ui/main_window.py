"""
Main application window.
"""
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from .components import (
    URLInput,
    FolderSelector,
    FileSelector,
    ProgressPanel,
    LogPanel,
    FormatSelector,
    PlatformIndicator,
)
from downloaders import (
    DownloadManager,
    DownloadConfig,
    DownloadProgress,
    OutputFormat,
)


class MainWindow(tk.Tk):
    """Main application window for the media downloader."""
    
    APP_TITLE = "Media Downloader"
    DEFAULT_SIZE = "750x520"
    MIN_SIZE = (750, 520)
    
    def __init__(self):
        super().__init__()
        
        self.title(self.APP_TITLE)
        self.geometry(self.DEFAULT_SIZE)
        self.minsize(*self.MIN_SIZE)
        
        self._downloading = False
        self._download_manager: Optional[DownloadManager] = None
        
        self._build_ui()
        self._setup_bindings()
        self._apply_theme()
    
    def _build_ui(self):
        """Build the user interface."""
        pad = {"padx": 12, "pady": 8}
        
        # Main container
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)
        
        # Header
        header = ttk.Frame(main)
        header.pack(fill="x", **pad)
        
        ttk.Label(
            header,
            text="📥 Media Downloader",
            font=("TkDefaultFont", 14, "bold")
        ).pack(side="left")
        
        platforms = DownloadManager.get_supported_platforms()
        ttk.Label(
            header,
            text=f"Soporta: {', '.join(platforms)}",
            foreground="#666"
        ).pack(side="right")
        
        # URL Input
        self.url_input = URLInput(main, label="URL del video:")
        self.url_input.pack(fill="x", **pad)
        
        # Platform indicator
        self.platform_indicator = PlatformIndicator(main)
        self.platform_indicator.pack(fill="x", padx=12, pady=(0, 8))
        
        # Output folder
        self.folder_selector = FolderSelector(
            main,
            label="Carpeta de salida:",
            default="./downloads"
        )
        self.folder_selector.pack(fill="x", **pad)
        
        # Cookies file (optional)
        self.cookies_selector = FileSelector(
            main,
            label="Cookies (opcional, para contenido privado):",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")]
        )
        self.cookies_selector.pack(fill="x", **pad)
        
        # Format selector
        format_frame = ttk.Frame(main)
        format_frame.pack(fill="x", **pad)
        
        ttk.Label(format_frame, text="Formato de salida:").pack(anchor="w")
        self.format_selector = FormatSelector(format_frame)
        self.format_selector.pack(anchor="w", pady=(6, 0))
        
        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", **pad)
        
        self.btn_download = ttk.Button(
            btn_frame,
            text="⬇ Descargar",
            command=self._start_download
        )
        self.btn_download.pack(side="left")
        
        self.btn_open_folder = ttk.Button(
            btn_frame,
            text="📁 Abrir carpeta",
            command=self._open_output_folder
        )
        self.btn_open_folder.pack(side="left", padx=(8, 0))
        
        self.btn_clear_log = ttk.Button(
            btn_frame,
            text="🗑 Limpiar log",
            command=lambda: self.log_panel.clear()
        )
        self.btn_clear_log.pack(side="right")
        
        # Progress
        self.progress_panel = ProgressPanel(main)
        self.progress_panel.pack(fill="x", **pad)
        
        # Log
        self.log_panel = LogPanel(main, label="Log:", height=8)
        self.log_panel.pack(fill="both", expand=True, **pad)
    
    def _setup_bindings(self):
        """Setup event bindings."""
        # Update platform indicator when URL changes
        self.url_input.url_var.trace_add("write", self._on_url_changed)
    
    def _apply_theme(self):
        """Apply visual theme."""
        try:
            style = ttk.Style()
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except Exception:
            pass
    
    def _on_url_changed(self, *args):
        """Handle URL input changes."""
        url = self.url_input.get()
        if url:
            manager = DownloadManager()
            platform = manager.detect_platform(url)
            self.platform_indicator.set_platform(platform)
        else:
            self.platform_indicator.set_platform("—")
    
    def _set_busy(self, busy: bool):
        """Enable/disable UI during download."""
        self._downloading = busy
        state = "disabled" if busy else "normal"
        
        self.url_input.set_state(state)
        self.folder_selector.set_state(state)
        self.cookies_selector.set_state(state)
        self.format_selector.set_state(state)
        self.btn_download.configure(state=state)
    
    def _handle_progress(self, progress: DownloadProgress):
        """Handle progress updates from downloader (called from worker thread)."""
        def update():
            self.progress_panel.set_progress(progress.percent)
            self.progress_panel.set_status(progress.message)
            
            if progress.status == "error":
                self.log_panel.log(f"❌ {progress.message}")
            elif progress.status == "finished":
                self.log_panel.log(f"✅ {progress.message}")
        
        self.after(0, update)
    
    def _start_download(self):
        """Start the download process."""
        url = self.url_input.get()
        output_dir = self.folder_selector.get()
        
        # Validation
        if not url:
            messagebox.showerror("Error", "Introduce una URL de video.")
            return
        
        if not output_dir:
            messagebox.showerror("Error", "Selecciona una carpeta de salida.")
            return
        
        # Create output directory
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"No se puede crear la carpeta:\n{e}")
            return
        
        # Prepare config
        config = DownloadConfig(
            url=url,
            output_dir=output_dir,
            output_format=OutputFormat.AUDIO if self.format_selector.is_audio() else OutputFormat.VIDEO,
            cookies_file=self.cookies_selector.get(),
        )
        
        # Log start
        self.log_panel.log(f"🔗 URL: {url}")
        self.log_panel.log(f"📁 Salida: {output_dir}")
        self.log_panel.log(f"🎬 Formato: {'MP3' if config.output_format == OutputFormat.AUDIO else 'MP4'}")
        
        # Start download in background thread
        self._set_busy(True)
        self.progress_panel.reset()
        
        thread = threading.Thread(
            target=self._download_worker,
            args=(config,),
            daemon=True
        )
        thread.start()
    
    def _download_worker(self, config: DownloadConfig):
        """Worker thread for downloading."""
        try:
            manager = DownloadManager(progress_callback=self._handle_progress)
            info = manager.download(config)
            
            title = info.get("title", "archivo")
            self.after(0, lambda: messagebox.showinfo(
                "Descarga completa",
                f"Se descargó: {title}"
            ))
            
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: messagebox.showerror(
                "Error de descarga",
                f"No se pudo descargar:\n\n{error_msg}"
            ))
        
        finally:
            self.after(0, lambda: self._set_busy(False))
    
    def _open_output_folder(self):
        """Open the output folder in file manager."""
        folder = self.folder_selector.get()
        if not folder:
            return
        
        try:
            os.makedirs(folder, exist_ok=True)
            
            if os.name == "nt":  # Windows
                os.startfile(folder)
            elif os.uname().sysname == "Darwin":  # macOS
                os.system(f'open "{folder}"')
            else:  # Linux
                os.system(f'xdg-open "{folder}"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}")
