# -*- mode: python ; coding: utf-8 -*-
"""
Spec PyInstaller — Anonymiseur Action Telecom
Génère : dist/Anonymiseur.exe (exécutable autonome Windows)
"""

import sys
from pathlib import Path

# ── Modèle spaCy ──────────────────────────────────────────
spacy_datas = []
try:
    import fr_core_news_md
    model_src = str(Path(fr_core_news_md.__file__).parent)
    spacy_datas = [(model_src, "fr_core_news_md")]
    print(f"[spec] Modèle spaCy : {model_src}")
except ImportError:
    print("[spec] WARN : fr_core_news_md introuvable — NER désactivé")

# ── Tesseract portable embarqué ───────────────────────────
# Place les binaires dans ./vendor/tesseract/ avant le build
tesseract_datas = []
vendor_tess = Path(SPECPATH) / "vendor" / "tesseract"
if (vendor_tess / "tesseract.exe").exists():
    tesseract_datas = [(str(vendor_tess), "tesseract")]
    print(f"[spec] Tesseract embarqué : {vendor_tess}")
else:
    print(f"[spec] WARN : vendor/tesseract/ absent — Tesseract NON embarqué")
    print(f"[spec]        Téléchargez Tesseract portable et placez-le dans {vendor_tess}")

block_cipher = None

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("templates",     "templates"),
        ("anonymizer.py", "."),
        ("ocr.py",        "."),
        ("paths.py",      "."),
        ("validators.py", "."),
        ("VERSION",       "."),
    ] + spacy_datas + tesseract_datas,
    hiddenimports=[
        "flask", "jinja2", "werkzeug", "click",
        "spacy", "spacy.lang.fr", "spacy.lang.fr.stop_words",
        "spacy.pipeline", "spacy.pipeline.ner",
        "fr_core_news_md",
        "thinc", "thinc.api", "thinc.backends",
        "cymem", "preshed", "murmurhash", "blis",
        "srsly", "catalogue", "wasabi", "typer",
        "confection", "pydantic",
        "pytesseract", "PIL", "PIL.Image",
        "fitz",
        "pypdf",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "numpy.testing"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Icône (optionnelle) : place icon.ico à la racine
icon_path = Path(SPECPATH) / "icon.ico"
icon_arg = str(icon_path) if icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Anonymiseur",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
    version="version_info.txt" if (Path(SPECPATH) / "version_info.txt").exists() else None,
)
