# Changelog

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).
Versionnement [SemVer](https://semver.org/lang/fr/).

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
