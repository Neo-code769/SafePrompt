"""
Module OCR — Extraction de texte depuis images et PDF scannés
=============================================================
Dépendances :
  - pytesseract  (wrapper Python pour Tesseract)
  - Pillow       (traitement d'images)
  - pymupdf      (rendu PDF → image, sans poppler)

Tesseract :
  - Cherche d'abord une version embarquée (sous-dossier `tesseract/`)
  - Sinon scan standard (Program Files, PATH, registre Windows)
  - Sinon chemin manuel sauvegardé dans %APPDATA%/ActionTelecom/Anonymiseur/config.json
"""

import io
import json
import logging
import subprocess
import sys
from pathlib import Path

from paths import bundled_resource, config_file

log = logging.getLogger(__name__)

OCR_PAGE_TIMEOUT_S = 30
OCR_MAX_PAGES = 50


# ─────────────────────────────────────────────────────
# Config persistante
# ─────────────────────────────────────────────────────

def _load_config() -> dict:
    try:
        return json.loads(config_file().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_config(data: dict):
    try:
        config_file().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        log.warning("Sauvegarde config échouée : %s", e)


# ─────────────────────────────────────────────────────
# Détection Tesseract
# ─────────────────────────────────────────────────────

def _bundled_tesseract() -> str | None:
    """Tesseract embarqué dans la distribution (PyInstaller / installeur)."""
    candidate = bundled_resource("tesseract/tesseract.exe")
    if candidate.exists():
        return str(candidate)
    return None


_STANDARD_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    str(Path.home() / r"AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    str(Path.home() / r"AppData\Local\Tesseract-OCR\tesseract.exe"),
    r"C:\Tesseract-OCR\tesseract.exe",
    r"C:\tools\Tesseract-OCR\tesseract.exe",
]


def _find_in_path() -> str | None:
    try:
        result = subprocess.run(
            ["where", "tesseract"] if sys.platform == "win32" else ["which", "tesseract"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            line = result.stdout.strip().splitlines()[0]
            if line and Path(line).exists():
                return line
    except Exception:
        pass
    return None


def _find_via_registry() -> str | None:
    if sys.platform != "win32":
        return None
    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for subkey in (r"SOFTWARE\Tesseract-OCR", r"SOFTWARE\WOW6432Node\Tesseract-OCR"):
                try:
                    with winreg.OpenKey(hive, subkey) as key:
                        install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                        candidate = Path(install_dir) / "tesseract.exe"
                        if candidate.exists():
                            return str(candidate)
                except (FileNotFoundError, OSError):
                    continue
    except ImportError:
        pass
    return None


def find_tesseract_auto() -> str | None:
    # 1. Embarqué (priorité absolue pour déploiement AT)
    found = _bundled_tesseract()
    if found:
        return found

    # 2. Config sauvegardée
    saved = _load_config().get("tesseract_path")
    if saved and Path(saved).exists():
        return saved

    # 3. Chemins standards
    for p in _STANDARD_PATHS:
        if Path(p).exists():
            return p

    # 4. PATH système
    found = _find_in_path()
    if found:
        return found

    # 5. Registre Windows
    return _find_via_registry()


# ─────────────────────────────────────────────────────
# État global
# ─────────────────────────────────────────────────────

_tesseract_path: str | None = None
_tesseract_available: bool = False
_tesseract_version: str | None = None


def configure_tesseract(custom_path: str | None = None) -> bool:
    global _tesseract_path, _tesseract_available, _tesseract_version
    try:
        import pytesseract
        path = custom_path or find_tesseract_auto()
        if path:
            pytesseract.pytesseract.tesseract_cmd = path
        _tesseract_version = str(pytesseract.get_tesseract_version())
        _tesseract_path = path or "tesseract"
        _tesseract_available = True
        if path:
            cfg = _load_config()
            cfg["tesseract_path"] = path
            _save_config(cfg)
        log.info("Tesseract OK : %s (v%s)", _tesseract_path, _tesseract_version)
        return True
    except Exception as e:
        log.warning("Tesseract indisponible : %s", e)
        _tesseract_available = False
        return False


configure_tesseract()


# ─────────────────────────────────────────────────────
# API publique
# ─────────────────────────────────────────────────────

def set_path(path: str) -> bool:
    if not Path(path).exists():
        return False
    return configure_tesseract(custom_path=path)


def is_available() -> bool:
    return _tesseract_available


def get_path() -> str | None:
    return _tesseract_path


def status_message() -> str:
    if _tesseract_available:
        return f"Tesseract {_tesseract_version} - OCR actif"
    return "Tesseract non trouvé — OCR désactivé"


def _require_tesseract():
    if not _tesseract_available:
        raise RuntimeError(
            "Tesseract n'est pas détecté. "
            "Configurez le chemin dans l'interface (Paramètres OCR) "
            "ou réinstallez l'Anonymiseur (Tesseract est embarqué)."
        )


# ─────────────────────────────────────────────────────
# Extraction OCR
# ─────────────────────────────────────────────────────

def ocr_image_bytes(image_bytes: bytes, lang: str = "fra+eng") -> str:
    _require_tesseract()
    import pytesseract
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    return pytesseract.image_to_string(
        image, lang=lang, config="--psm 6", timeout=OCR_PAGE_TIMEOUT_S
    ).strip()


def ocr_pdf_bytes(pdf_bytes: bytes, lang: str = "fra+eng", dpi: int = 300) -> str:
    _require_tesseract()
    import fitz
    import pytesseract
    from PIL import Image

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)
    if page_count > OCR_MAX_PAGES:
        doc.close()
        raise ValueError(
            f"PDF trop volumineux pour OCR : {page_count} pages "
            f"(maximum {OCR_MAX_PAGES})."
        )

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pages_text = []

    for page_num in range(page_count):
        pix = doc[page_num].get_pixmap(matrix=matrix, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        try:
            text = pytesseract.image_to_string(
                img, lang=lang, config="--psm 6", timeout=OCR_PAGE_TIMEOUT_S
            ).strip()
        except RuntimeError as e:
            log.warning("Page %d OCR timeout : %s", page_num + 1, e)
            text = ""
        if text:
            pages_text.append(f"--- Page {page_num + 1} ---\n{text}")

    doc.close()
    return "\n\n".join(pages_text) if pages_text else ""
