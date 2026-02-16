# Media Downloader

Aplicación modular para descargar videos y audio de **YouTube**, **X (Twitter)** e **Instagram**.

## Estructura del proyecto

```
media_downloader/
├── main.py                 # Punto de entrada
├── __main__.py             # Para ejecutar como módulo
├── requirements.txt        # Dependencias
├── downloaders/            # Módulo de descargadores
│   ├── __init__.py
│   ├── base.py             # Clase base abstracta
│   ├── manager.py          # Gestor que selecciona el descargador
│   ├── youtube.py          # Descargador YouTube
│   ├── twitter.py          # Descargador X/Twitter
│   └── instagram.py        # Descargador Instagram
└── ui/                     # Módulo de interfaz gráfica
    ├── __init__.py
    ├── main_window.py      # Ventana principal
    └── components.py       # Componentes reutilizables
```

## Instalación

```bash
# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# En Debian/Ubuntu, si no tienes tkinter:
sudo apt install python3-tk
```

## Uso

```bash
# Ejecutar la aplicación
python main.py

# O como módulo
python -m media_downloader
```

## Características

- **Multi-plataforma**: YouTube, X (Twitter), Instagram
- **Formatos**: Video (MP4) o solo audio (MP3)
- **Detección automática**: Identifica la plataforma según la URL
- **Cookies opcionales**: Para contenido que requiere login
- **FFmpeg incluido**: Via `imageio-ffmpeg` (o usa el del sistema)

## Añadir nuevas plataformas

1. Crear archivo en `downloaders/` (ej: `tiktok.py`)
2. Heredar de `BaseDownloader`
3. Implementar `_get_platform_options()`
4. Añadir a `DOWNLOADERS` en `manager.py`

Ejemplo:

```python
from .base import BaseDownloader, DownloadConfig, OutputFormat

class TikTokDownloader(BaseDownloader):
    PLATFORM_NAME = "TikTok"
    SUPPORTED_DOMAINS = ["tiktok.com", "vm.tiktok.com"]
    
    def _get_platform_options(self, config: DownloadConfig) -> dict:
        # Opciones específicas de TikTok
        return {"format": "best"}
```

## Notas

- Instagram puede requerir cookies para contenido privado
- La calidad máxima depende de tener FFmpeg disponible
- X/Twitter a veces requiere cookies para tweets protegidos
