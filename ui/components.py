"""
Reusable UI components for the media downloader.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional


class URLInput(ttk.Frame):
    """URL input component with paste and clear buttons."""
    
    def __init__(self, parent, label: str = "URL:", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.url_var = tk.StringVar()
        
        # Label
        ttk.Label(self, text=label).pack(anchor="w")
        
        # Input row
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(6, 0))
        
        self.entry = ttk.Entry(row, textvariable=self.url_var)
        self.entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(row, text="Pegar", command=self._paste).pack(side="left", padx=(8, 0))
        ttk.Button(row, text="Limpiar", command=self._clear).pack(side="left", padx=(8, 0))
    
    def _paste(self):
        try:
            text = self.clipboard_get()
            self.url_var.set(text.strip())
        except tk.TclError:
            messagebox.showwarning("Portapapeles", "No hay nada en el portapapeles.")
    
    def _clear(self):
        self.url_var.set("")
    
    def get(self) -> str:
        return self.url_var.get().strip()
    
    def set(self, value: str):
        self.url_var.set(value)
    
    def set_state(self, state: str):
        self.entry.configure(state=state)


class FolderSelector(ttk.Frame):
    """Folder selection component."""
    
    def __init__(self, parent, label: str = "Carpeta:", default: str = "./downloads", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.folder_var = tk.StringVar(value=default)
        
        # Label
        ttk.Label(self, text=label).pack(anchor="w")
        
        # Input row
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(6, 0))
        
        self.entry = ttk.Entry(row, textvariable=self.folder_var)
        self.entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(row, text="Elegir…", command=self._browse).pack(side="left", padx=(8, 0))
    
    def _browse(self):
        path = filedialog.askdirectory(
            title="Elige carpeta de salida",
            initialdir=self.folder_var.get() or "."
        )
        if path:
            self.folder_var.set(path)
    
    def get(self) -> str:
        return self.folder_var.get().strip()
    
    def set(self, value: str):
        self.folder_var.set(value)
    
    def set_state(self, state: str):
        self.entry.configure(state=state)


class FileSelector(ttk.Frame):
    """File selection component (for cookies, etc.)."""
    
    def __init__(
        self,
        parent,
        label: str = "Archivo:",
        filetypes: list = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.file_var = tk.StringVar()
        self.filetypes = filetypes or [("All files", "*.*")]
        
        # Label
        ttk.Label(self, text=label).pack(anchor="w")
        
        # Input row
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(6, 0))
        
        self.entry = ttk.Entry(row, textvariable=self.file_var)
        self.entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(row, text="Seleccionar…", command=self._browse).pack(side="left", padx=(8, 0))
    
    def _browse(self):
        path = filedialog.askopenfilename(
            title="Selecciona archivo",
            filetypes=self.filetypes
        )
        if path:
            self.file_var.set(path)
    
    def get(self) -> Optional[str]:
        value = self.file_var.get().strip()
        return value if value else None
    
    def set(self, value: str):
        self.file_var.set(value)
    
    def set_state(self, state: str):
        self.entry.configure(state=state)


class ProgressPanel(ttk.Frame):
    """Progress bar and status display."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Listo.")
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            mode="determinate"
        )
        self.progress_bar.pack(fill="x")
        
        # Status label
        ttk.Label(
            self,
            textvariable=self.status_var,
            foreground="#555"
        ).pack(anchor="w", pady=(6, 0))
    
    def set_progress(self, value: float):
        self.progress_var.set(max(0, min(100, value)))
    
    def set_status(self, text: str):
        self.status_var.set(text)
    
    def reset(self):
        self.set_progress(0)
        self.set_status("Listo.")


class LogPanel(ttk.Frame):
    """Scrollable log display."""
    
    def __init__(self, parent, label: str = "Log:", height: int = 8, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Label
        ttk.Label(self, text=label).pack(anchor="w")
        
        # Text widget with scrollbar
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, pady=(6, 0))
        
        self.text = tk.Text(container, height=height, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.text.yview)
        
        self.text.configure(yscrollcommand=scrollbar.set)
        
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def log(self, message: str):
        """Add a line to the log."""
        self.text.configure(state="normal")
        self.text.insert("end", message + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")
    
    def clear(self):
        """Clear the log."""
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


class FormatSelector(ttk.Frame):
    """Output format selector (video/audio)."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.format_var = tk.StringVar(value="video")
        
        ttk.Radiobutton(
            self,
            text="Video (MP4)",
            variable=self.format_var,
            value="video"
        ).pack(side="left")
        
        ttk.Radiobutton(
            self,
            text="Solo Audio (MP3)",
            variable=self.format_var,
            value="audio"
        ).pack(side="left", padx=(16, 0))
    
    def get(self) -> str:
        return self.format_var.get()
    
    def is_audio(self) -> bool:
        return self.format_var.get() == "audio"
    
    def set_state(self, state: str):
        for child in self.winfo_children():
            child.configure(state=state)


class PlatformIndicator(ttk.Frame):
    """Shows detected platform from URL."""
    
    PLATFORM_COLORS = {
        "YouTube": "#FF0000",
        "X (Twitter)": "#1DA1F2",
        "Instagram": "#E1306C",
        "Desconocida": "#999999",
    }
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.platform_var = tk.StringVar(value="Plataforma: —")
        
        self.label = ttk.Label(
            self,
            textvariable=self.platform_var,
            font=("TkDefaultFont", 9, "bold")
        )
        self.label.pack(anchor="w")
    
    def set_platform(self, platform: str):
        self.platform_var.set(f"Plataforma: {platform}")
