"""
Chemins applicatifs — Anonymiseur Action Telecom
=================================================
Centralise les emplacements de config et logs dans %APPDATA%.
"""

import os
import sys
from pathlib import Path

APP_VENDOR = "ActionTelecom"
APP_NAME = "Anonymiseur"


def app_data_dir() -> Path:
    """Dossier de données utilisateur (créé si absent)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".config"
    d = base / APP_VENDOR / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def local_data_dir() -> Path:
    """Dossier local (logs, cache)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    d = base / APP_VENDOR / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_file() -> Path:
    return app_data_dir() / "config.json"


def logs_dir() -> Path:
    d = local_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def bundled_resource(relative: str) -> Path:
    """Ressource embarquée (PyInstaller _MEIPASS ou dossier projet)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).parent / relative
