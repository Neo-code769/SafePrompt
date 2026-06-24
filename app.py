"""
Interface Web — Anonymiseur de données sensibles
================================================
Action Telecom — usage local par poste.
Lance : python app.py  →  http://127.0.0.1:<port>
"""

import hashlib
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
from collections import OrderedDict
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

import crypto as crypto_module
import ocr as ocr_module
from anonymizer import Anonymizer
from paths import bundled_resource, config_file, logs_dir

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
# Cache LRU anonymisation (par hash texte + mapping + catégories)
# ─────────────────────────────────────────────

_CACHE_MAX = int(os.environ.get("ANONYMISEUR_CACHE_SIZE", "32"))
_anon_cache: "OrderedDict[str, dict]" = OrderedDict()
_cache_lock = threading.Lock()


def _cache_key(
    text: str,
    mapping_raw: bytes,
    disabled_cats: tuple[str, ...],
    whitelist: tuple[str, ...],
) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(b"\0")
    h.update(mapping_raw)
    h.update(b"\0")
    h.update("|".join(disabled_cats).encode("utf-8"))
    h.update(b"\0")
    h.update("|".join(whitelist).encode("utf-8"))
    return h.hexdigest()


def _cache_get(key: str) -> dict | None:
    with _cache_lock:
        entry = _anon_cache.get(key)
        if entry is not None:
            _anon_cache.move_to_end(key)
        return entry


def _cache_put(key: str, value: dict) -> None:
    with _cache_lock:
        _anon_cache[key] = value
        _anon_cache.move_to_end(key)
        while len(_anon_cache) > _CACHE_MAX:
            _anon_cache.popitem(last=False)


# ─────────────────────────────────────────────
# Catégories actives (config persistant)
# ─────────────────────────────────────────────

ALL_CATEGORIES = [
    "CB", "NIR", "IBAN", "SIRET", "SIREN", "EMAIL", "MAC", "IPv6", "IPv4",
    "TEL", "HOSTNAME", "CODE_POSTAL", "PORT", "DATE_NAISSANCE",
    "PERSONNE", "ORGANISATION", "LIEU", "DIVERS",
]


def _read_config() -> dict:
    try:
        path = config_file()
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("Lecture config échouée : %s", e)
    return {}


def _write_config(cfg: dict) -> None:
    path = config_file()
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_disabled_categories() -> tuple[str, ...]:
    cfg = _read_config()
    return tuple(sorted(cfg.get("disabled_categories", [])))


def _get_ner_whitelist() -> tuple[str, ...]:
    cfg = _read_config()
    raw = cfg.get("ner_whitelist", [])
    if not isinstance(raw, list):
        return ()
    cleaned = sorted({str(w).strip() for w in raw if str(w).strip()})
    return tuple(cleaned)


def _invalidate_cache() -> None:
    with _cache_lock:
        _anon_cache.clear()

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


@app.route("/categories", methods=["GET"])
def get_categories():
    disabled = list(_get_disabled_categories())
    return jsonify(all=ALL_CATEGORIES, disabled=disabled)


@app.route("/categories", methods=["POST"])
def set_categories():
    data = request.get_json(force=True)
    disabled = data.get("disabled", [])
    if not isinstance(disabled, list) or not all(isinstance(c, str) for c in disabled):
        return jsonify(error="Format invalide."), 400
    unknown = [c for c in disabled if c not in ALL_CATEGORIES]
    if unknown:
        return jsonify(error=f"Catégorie inconnue : {', '.join(unknown)}"), 400
    cfg = _read_config()
    cfg["disabled_categories"] = sorted(set(disabled))
    try:
        _write_config(cfg)
    except Exception as e:
        log.error("Écriture config échouée : %s", e)
        return jsonify(error="Impossible d'enregistrer la configuration."), 500
    _invalidate_cache()
    log.info("Catégories désactivées : %s", cfg["disabled_categories"])
    return jsonify(success=True, disabled=cfg["disabled_categories"])


@app.route("/ner-whitelist", methods=["GET"])
def get_ner_whitelist():
    return jsonify(whitelist=list(_get_ner_whitelist()))


@app.route("/ner-whitelist", methods=["POST"])
def set_ner_whitelist():
    data = request.get_json(force=True)
    items = data.get("whitelist", [])
    if not isinstance(items, list) or not all(isinstance(w, str) for w in items):
        return jsonify(error="Format invalide."), 400
    cleaned = sorted({w.strip() for w in items if w.strip()})
    if len(cleaned) > 500:
        return jsonify(error="Maximum 500 entrées."), 400
    if any(len(w) > 200 for w in cleaned):
        return jsonify(error="Chaque entrée doit faire ≤ 200 caractères."), 400
    cfg = _read_config()
    cfg["ner_whitelist"] = cleaned
    try:
        _write_config(cfg)
    except Exception as e:
        log.error("Écriture whitelist échouée : %s", e)
        return jsonify(error="Impossible d'enregistrer."), 500
    _invalidate_cache()
    log.info("NER whitelist : %d entrées", len(cleaned))
    return jsonify(success=True, whitelist=cleaned)


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

    raw_map = b""
    mapping_file = None
    if "mapping" in request.files and request.files["mapping"].filename != "":
        raw_map = request.files["mapping"].read()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="wb")
        tmp.write(raw_map)
        tmp.close()
        mapping_file = tmp.name

    disabled_cats = _get_disabled_categories()
    whitelist = _get_ner_whitelist()
    cache_key = _cache_key(text, raw_map, disabled_cats, whitelist)
    cached = _cache_get(cache_key)
    if cached is not None:
        log.info("Anonymisation cache HIT : fichier=%s", upload.filename)
        if mapping_file:
            try:
                os.unlink(mapping_file)
            except OSError:
                pass
        return jsonify(
            original=text,
            anonymized=cached["anonymized"],
            summary=cached["summary"],
            mapping=cached["mapping"],
            filename=_anon_filename(upload.filename),
            method=method,
            cached=True,
        )

    try:
        anon = Anonymizer(
            mapping_file=mapping_file,
            disabled_categories=disabled_cats,
            ner_whitelist=whitelist,
        )
        result = anon.anonymize(text)
        summary = _build_summary(anon)
        mapping_data = anon.mapping
    finally:
        if mapping_file:
            try:
                os.unlink(mapping_file)
            except OSError:
                pass

    _cache_put(cache_key, {"anonymized": result, "summary": summary, "mapping": mapping_data})

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

    # Déchiffrement si mapping chiffré
    try:
        map_json = json.loads(raw_map)
        if crypto_module.is_encrypted(map_json):
            password = request.form.get("password", "")
            if not password:
                return jsonify(error="Ce mapping est chiffré. Fournissez le mot de passe."), 422
            try:
                map_json = crypto_module.decrypt_mapping(map_json, password)
                raw_map = json.dumps(map_json, ensure_ascii=False).encode("utf-8")
            except Exception:
                return jsonify(error="Mot de passe incorrect ou mapping corrompu."), 422
    except (json.JSONDecodeError, ValueError):
        pass  # fichier non-JSON, l'Anonymizer tentera de le charger normalement

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


@app.route("/download-mapping-encrypted", methods=["POST"])
def download_mapping_encrypted():
    data = request.get_json(force=True)
    mapping = data.get("mapping", {})
    password = data.get("password", "")
    if not password:
        return jsonify(error="Mot de passe requis pour le chiffrement."), 400
    full_map = {"mapping": mapping, "reverse_mapping": {v: k for k, v in mapping.items()}}
    try:
        enc = crypto_module.encrypt_mapping(full_map, password)
    except Exception as e:
        log.error("Chiffrement mapping échoué : %s", e)
        return jsonify(error="Erreur de chiffrement."), 500
    content = json.dumps(enc, ensure_ascii=False, indent=2)
    buf = io.BytesIO(content.encode("utf-8"))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="mapping.encrypted.json",
                     mimetype="application/json")


# ─────────────────────────────────────────────
# Admin
# ─────────────────────────────────────────────

_ADMIN_KEY = os.environ.get("ANONYMISEUR_ADMIN_KEY", "").strip()


def _admin_auth(f):
    """Restreint les routes admin : localhost uniquement, ou clé via X-Admin-Key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        remote = request.remote_addr or ""
        if remote in ("127.0.0.1", "::1"):
            return f(*args, **kwargs)
        if _ADMIN_KEY and request.headers.get("X-Admin-Key") == _ADMIN_KEY:
            return f(*args, **kwargs)
        return jsonify(error="Accès refusé."), 403
    return decorated


@app.route("/admin/info")
@_admin_auth
def admin_info():
    log_size = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
    log_lines: list[str] = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, encoding="utf-8", errors="replace") as f:
                log_lines = [line.rstrip() for line in f.readlines()[-100:]]
        except Exception:
            pass
    cfg: dict = {}
    cfg_path = config_file()
    try:
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return jsonify(
        log_path=str(LOG_FILE),
        log_size=log_size,
        log_lines=log_lines,
        config_path=str(cfg_path),
        config=cfg,
        version=_read_version(),
    )


@app.route("/admin/purge-logs", methods=["POST"])
@_admin_auth
def admin_purge_logs():
    try:
        LOG_FILE.write_text("", encoding="utf-8")
        log.info("Logs purgés via interface admin")
        return jsonify(success=True)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/admin/reset-config", methods=["POST"])
@_admin_auth
def admin_reset_config():
    try:
        cfg_path = config_file()
        if cfg_path.exists():
            cfg_path.unlink()
        log.info("Config réinitialisée via interface admin")
        return jsonify(success=True)
    except Exception as e:
        return jsonify(error=str(e)), 500


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _read_version() -> str:
    try:
        path = bundled_resource("VERSION")
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return "?"


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
