#!/usr/bin/env python3
"""
Media Downloader - Download videos and audio from YouTube, X (Twitter), and Instagram.

Usage:
    python main.py
    
Or as a module:
    python -m media_downloader
"""
import sys
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ui import MainWindow


def main():
    """Main entry point."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
