"""
Interface Web — Anonymiseur de données sensibles
================================================
Action Telecom — usage local par poste.
Lance : python app.py  →  http://127.0.0.1:<port>
"""

import io
import json
import logging
import os
import secrets
import socket
import sys
import tempfile
import threading
import webbrowser
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from anonymizer import Anonymizer
import ocr as ocr_module
from paths import bundled_resource, logs_dir

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────

LOG_FILE = logs_dir() / "anonymiseur.log"
log_level = os.environ.get("ANONYMISEUR_LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
log = logging.getLogger("app")

# ─────────────────────────────────────────────
# Flask
# ─────────────────────────────────────────────

BASE_DIR = bundled_resource("")

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 Mo max
app.config["SECRET_KEY"] = secrets.token_hex(32)  # régénéré à chaque démarrage (local)

DEFAULT_PORT = 7777

# ─────────────────────────────────────────────
# Extensions autorisées
# ─────────────────────────────────────────────

TEXT_EXTENSIONS = {
    "txt", "log", "csv", "json", "xml", "html", "md",
    "cfg", "ini", "conf", "yaml", "yml", "toml",
}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tiff", "tif", "webp", "gif"}
PDF_EXTENSION = {"pdf"}
ALL_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS | PDF_EXTENSION


def file_ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def allowed_file(filename: str) -> bool:
    return file_ext(filename) in ALL_EXTENSIONS


# ─────────────────────────────────────────────
# Lecture / extraction
# ─────────────────────────────────────────────

def read_upload(file) -> tuple[str, str]:
    filename = file.filename or ""
    ext = file_ext(filename)
    raw = file.read()

    if ext in IMAGE_EXTENSIONS:
        if not ocr_module.is_available():
            raise RuntimeError(ocr_module.status_message())
        text = ocr_module.ocr_image_bytes(raw)
        if not text:
            raise ValueError("Aucun texte détecté dans l'image.")
        return text, "OCR (image)"

    if ext == "pdf":
        return _read_pdf(raw)

    try:
        return raw.decode("utf-8"), "texte"
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "texte"


def _read_pdf(raw: bytes) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        pages = []
        for i, page in enumerate(reader.pages, 1):
            t = (page.extract_text() or "").strip()
            if t:
                pages.append(f"--- Page {i} ---\n{t}")
        if pages:
            return "\n\n".join(pages), "PDF natif (pypdf)"
    except Exception as e:
        log.debug("Extraction pypdf échouée : %s", e)

    if not ocr_module.is_available():
        raise RuntimeError(
            "Ce PDF ne contient pas de texte extractible (PDF scanné).\n"
            "Tesseract est requis pour l'OCR.\n"
            + ocr_module.status_message()
        )
    text = ocr_module.ocr_pdf_bytes(raw)
    if not text:
        raise ValueError("Aucun texte détecté dans le PDF (même après OCR).")
    return text, "OCR (PDF scanné)"


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    return jsonify(
        ocr_available=ocr_module.is_available(),
        ocr_status=ocr_module.status_message(),
        tesseract_path=ocr_module.get_path() or "",
    )


@app.route("/set-tesseract", methods=["POST"])
def set_tesseract():
    data = request.get_json(force=True)
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify(error="Chemin vide."), 400
    ok = ocr_module.set_path(path)
    if ok:
        return jsonify(
            success=True,
            ocr_status=ocr_module.status_message(),
            tesseract_path=ocr_module.get_path(),
        )
    return jsonify(error=f"Fichier introuvable ou non fonctionnel : {path}"), 422


@app.route("/anonymize", methods=["POST"])
def anonymize():
    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify(error="Aucun fichier fourni."), 400

    upload = request.files["file"]
    if not allowed_file(upload.filename):
        return jsonify(
            error=f"Extension non supportée. Acceptés : {', '.join(sorted(ALL_EXTENSIONS))}"
        ), 400

    try:
        text, method = read_upload(upload)
    except (ValueError, RuntimeError) as e:
        log.info("Lecture refusée : %s", e)
        return jsonify(error=str(e)), 422

    mapping_file = None
    if "mapping" in request.files and request.files["mapping"].filename != "":
        raw_map = request.files["mapping"].read()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="wb")
        tmp.write(raw_map)
        tmp.close()
        mapping_file = tmp.name

    try:
        anon = Anonymizer(mapping_file=mapping_file)
        result = anon.anonymize(text)
        summary = _build_summary(anon)
        mapping_data = anon.mapping
    finally:
        if mapping_file:
            try:
                os.unlink(mapping_file)
            except OSError:
                pass

    log.info(
        "Anonymisation OK : fichier=%s méthode=%s entités=%d",
        upload.filename, method, len(mapping_data),
    )

    return jsonify(
        original=text,
        anonymized=result,
        summary=summary,
        mapping=mapping_data,
        filename=_anon_filename(upload.filename),
        method=method,
    )


@app.route("/deanonymize", methods=["POST"])
def deanonymize():
    if "file" not in request.files or request.files["file"].filename == "":
        return jsonify(error="Aucun fichier fourni."), 400
    if "mapping" not in request.files or request.files["mapping"].filename == "":
        return jsonify(error="Le fichier mapping.json est requis pour dé-anonymiser."), 400

    try:
        text, _ = read_upload(request.files["file"])
    except (ValueError, RuntimeError) as e:
        return jsonify(error=str(e)), 422

    raw_map = request.files["mapping"].read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="wb")
    tmp.write(raw_map)
    tmp.close()

    try:
        anon = Anonymizer(mapping_file=tmp.name)
        result = anon.deanonymize(text)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    return jsonify(
        original=text,
        anonymized=result,
        filename=request.files["file"].filename.replace("_anonymise", ""),
    )


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json(force=True)
    content = data.get("content", "")
    filename = Path(data.get("filename", "anonymise.txt")).stem + ".txt"
    buf = io.BytesIO(content.encode("utf-8"))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=filename,
                     mimetype="text/plain; charset=utf-8")


@app.route("/download-mapping", methods=["POST"])
def download_mapping():
    data = request.get_json(force=True)
    mapping = data.get("mapping", {})
    content = json.dumps(
        {"mapping": mapping, "reverse_mapping": {v: k for k, v in mapping.items()}},
        ensure_ascii=False, indent=2,
    )
    buf = io.BytesIO(content.encode("utf-8"))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="mapping.json",
                     mimetype="application/json")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _anon_filename(original: str) -> str:
    return f"{Path(original).stem}_anonymise.txt"


def _build_summary(anon: Anonymizer) -> list[dict]:
    by_cat: dict[str, list] = {}
    for original, tag in anon.mapping.items():
        cat = tag.split("_")[0].strip("[")
        by_cat.setdefault(cat, []).append({"tag": tag, "original": original})
    return [
        {"category": cat, "items": sorted(items, key=lambda x: x["tag"])}
        for cat, items in sorted(by_cat.items())
    ]


def _find_free_port(preferred: int = DEFAULT_PORT) -> int:
    """Retourne le port préféré s'il est libre, sinon un port aléatoire."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _launch_browser(port: int, delay: float = 1.0):
    def _open():
        try:
            webbrowser.open(f"http://127.0.0.1:{port}")
        except Exception as e:
            log.warning("Ouverture navigateur échouée : %s", e)
    threading.Timer(delay, _open).start()


# ─────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────

def main():
    port = _find_free_port(DEFAULT_PORT)
    print("=" * 52)
    print("  Anonymiseur de données — Action Telecom")
    print(f"  URL   : http://127.0.0.1:{port}")
    print(f"  OCR   : {ocr_module.status_message()}".encode("ascii", "replace").decode("ascii"))
    print(f"  Logs  : {LOG_FILE}")
    print("=" * 52)
    log.info("Démarrage sur port %d", port)

    no_browser = os.environ.get("ANONYMISEUR_NO_BROWSER", "").lower() in ("1", "true", "yes")
    if not no_browser:
        _launch_browser(port)

    app.run(debug=False, host="127.0.0.1", port=port, use_reloader=False)


if __name__ == "__main__":
    main()
