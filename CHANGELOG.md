# Changelog

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Versionnement [SemVer](https://semver.org/lang/fr/).

## [1.2.0] - 2026-06-24

### Ajouté
- Détection `DATE_NAISSANCE` (regex + mot-clé proximité : `né(e) le`, `DOB`, `born on`, …).
- Toggles par catégorie via UI (endpoint `/categories`, persisté dans `config.json`).
- Liste blanche NER (endpoint `/ner-whitelist`, max 500 entrées) — match insensible à la casse, limites de mot.
- Cache LRU thread-safe sur `/anonymize`, keyé SHA-256 (texte + mapping + catégories + whitelist). Taille via `ANONYMISEUR_CACHE_SIZE`.
- Refonte UI complète Direction B Action Telecom (stepper dynamique, palette PII étendue à 18 catégories distinctes, dropzone, toggles sp-switch).
- Polices locales embarquées : Space Grotesk, Hanken Grotesk, JetBrains Mono (offline-safe, `static/fonts/`).
- CI GitHub Actions : Ubuntu + Windows × Python 3.11/3.12, ruff + pytest.
- `pytest-cov` avec rapport de couverture, seuil plancher 35 % (cible 80 %).
- `ruff` lint configuré.
- Filtre NER min length (≥ 2 caractères).
- Tests : 14 cas `DATE_NAISSANCE`, 9 cas qualité NER (whitelist, min length, anti-double-wrap).

### Modifié
- `NER` ignore désormais les tags existants `[CATEGORY_N]` (correction du double-wrapping spaCy).
- `print()` remplacés par `logging` dans `anonymizer.py`.
- `Path("VERSION")` remplacé par `bundled_resource("VERSION")` (compatible PyInstaller hors-dossier).
- Flask `static_folder` configuré via `bundled_resource("static")` (CSS + fonts servis correctement en dev et en bundle).
- `anonymizer.spec` : ajout `static/` aux `datas`.

### Sécurité
- Toujours aucun appel sortant (Google Fonts retiré, fonts locales).

## [1.0.0] - 2026-06-23

### Ajouté
- Module `paths.py` centralisant config et logs dans `%APPDATA%` / `%LOCALAPPDATA%`.
- Module `validators.py` : Luhn (CB), MOD-97 (IBAN), clé de contrôle NIR.
- Suite pytest (22 tests, validateurs + roundtrip).
- Logging fichier avec rotation (`logs/anonymiseur.log`).
- Ouverture automatique du navigateur au démarrage.
- Détection de port libre (fallback si 7777 occupé).
- Support Tesseract embarqué (sous-dossier `tesseract/` dans la distribution).
- Timeout OCR par page + limite à 50 pages.
- Script Inno Setup pour installeur Windows MSI-like.
- Métadonnées de version dans l'exécutable Windows.
- `.gitignore`, `README.md`, `CHANGELOG.md`, `VERSION`.

### Modifié
- Ordre des regex : MAC avant IPv6 (évite faux positifs sur adresses MAC).
- `config.json` déplacé hors du repo (chemin perso retiré).
- Réduction faux positifs : PAN/IBAN/NIR validés avant remplacement.
- Spec PyInstaller : ajout `paths.py`, `validators.py`, `VERSION`, icône optionnelle.

### Retiré
- `README.html` (remplacé par `README.md`).
- `config.json` versionné (déplacé dans `%APPDATA%`).
- Dossier `INCOGNITO/` vide.

## [0.x] - antérieur

Versions de prototypage non publiées.
