<img width="2357" height="1421" alt="Gemini_Generated_Image_ph1nniph1nniph1n(2)(1)(1)" src="https://github.com/user-attachments/assets/f6cf90f7-4245-4444-8fc0-060bc3a4b0fe" />

# Safe Prompt — Anonymiseur de données sensibles · Action Telecom

Outil d'anonymisation de textes, logs, PDF et images avant soumission à un service d'IA externe (ChatGPT, Claude, Mistral, etc.). Traitement 100 % local ou intranet, aucune donnée ne sort du SI.

**Version actuelle : 1.2.0**

## Fonctionnalités

### Détection PII
- Regex : emails, IPv4/IPv6, MAC, téléphones FR, codes postaux, IBAN, CB, NIR, SIRET, SIREN, hostnames internes, ports, **dates de naissance** (mot-clé proximité).
- Validation algorithmique : Luhn (CB, SIRET, SIREN), MOD-97 (IBAN), clé de contrôle (NIR) — réduit fortement les faux positifs.
- NER spaCy FR : personnes, organisations, lieux, divers (`fr_core_news_md`).

### Configuration utilisateur (nouveau v1.2)
- **Toggles par catégorie** : activer/désactiver chaque type de PII depuis l'UI. Persisté dans `config.json`, appliqué côté serveur.
- **Liste blanche NER** : termes à ne jamais anonymiser (noms d'entreprises clientes, marques). Match insensible à la casse, limites de mot (regex `\b…\b`).
- Autosave debounced (UI ↔ backend).

### Performance (nouveau v1.2)
- **Cache LRU thread-safe** sur `/anonymize`, keyed par SHA-256 (texte + mapping + catégories + whitelist).
- Invalidation automatique à tout changement de configuration.
- Taille configurable via `ANONYMISEUR_CACHE_SIZE` (défaut 32).

### Interface (refonte v1.2)
- Refonte complète **Direction B « Parcours »** (charte Action Telecom).
- Polices embarquées localement (offline-safe) : Space Grotesk, Hanken Grotesk, JetBrains Mono.
- Stepper dynamique branché à l'état (Déposer → Personnaliser → Récupérer).
- Palette PII étendue : un ton distinct par catégorie (18 PII, plus aucune collision visuelle).
- Drag-and-drop, copie presse-papier, téléchargement texte + mapping.

### OCR
- Tesseract pour images et PDF scannés. Configuration UI guidée.

### Sécurité
- Chiffrement AES-256-GCM du mapping (PBKDF2-SHA256, 480 000 itérations).
- Mapping de session (sessionStorage) chargé automatiquement à l'onglet *Dé-anonymiser*.
- Aucun fichier client persisté sur disque (uploads en mémoire, temporaires supprimés).

### Admin
- Consultation des 100 dernières lignes de log, purge, réinitialisation de la configuration.
- Restriction localhost ou clé `X-Admin-Key` en intranet.

### Déploiement
- Poste unique (installeur `.exe` Inno Setup) ou serveur intranet partagé.

### Qualité (nouveau v1.2)
- **CI GitHub Actions** : Ubuntu + Windows × Python 3.11 / 3.12, ruff + pytest.
- **pytest-cov** avec rapport de couverture.
- **ruff** lint configuré.
- Logging structuré (remplace `print`).

## Public visé

Techniciens, commerciaux et administratifs d'Action Telecom qui doivent partager des extraits de logs, tickets ou échanges client avec un assistant IA sans divulguer de données sensibles.

## Installation poste utilisateur

### Option 1 — Installeur (recommandé)

1. Récupérer `Anonymiseur-Setup-1.2.0.exe` (généré par `build_installer.bat`).
2. Double-cliquer → suivant → terminer.
3. Lancer via le menu Démarrer : *Action Telecom → Anonymiseur*. Le navigateur s'ouvre automatiquement.

Tesseract et les polices sont embarqués dans l'installeur — aucune dépendance externe à l'exécution.

### Option 2 — Lancement depuis les sources (dev)

```bat
install.bat       :: dépendances Python + modèle spaCy + tests
python app.py     :: lance l'interface web
```

Ouvre `http://127.0.0.1:7777` (ou un port libre si 7777 occupé).

### Option 3 — Hébergement intranet partagé

Permet à tous les collaborateurs d'accéder à l'outil via navigateur, sans installation sur chaque poste.

Voir la procédure complète : [docs/migration-intranet-option-a.md](docs/migration-intranet-option-a.md)

## Utilisation

1. Glisser un fichier (`.txt`, `.log`, `.pdf`, `.png`, `.jpg`, ...).
2. Ajuster (optionnel) les catégories à masquer et la liste blanche.
3. Cliquer *Anonymiser*.
4. Récupérer le texte anonymisé (bouton télécharger ou copier).
5. Optionnel : télécharger le `mapping.json` (clair ou chiffré avec mot de passe) pour pouvoir restaurer le texte original.
6. Pour restaurer : onglet *Dé-anonymiser*, fournir le texte anonymisé + le `mapping.json`. Le mapping de la dernière session est chargé automatiquement.

## Emplacements de fichiers

| Quoi | Où |
|---|---|
| Config (catégories désactivées, liste blanche, chemin Tesseract) | `%APPDATA%\ActionTelecom\Anonymiseur\config.json` |
| Logs | `%LOCALAPPDATA%\ActionTelecom\Anonymiseur\logs\anonymiseur.log` |
| Exécutable | `C:\Program Files\ActionTelecom\Anonymiseur\` |

Aucun fichier client n'est persisté sur disque : uploads en mémoire, fichiers temporaires supprimés en fin de requête.

## Catégories détectées

| Tag | Type | Validation |
|---|---|---|
| `[EMAIL_n]` | Adresse mail | regex |
| `[IPv4_n]` / `[IPv6_n]` | IP | regex |
| `[MAC_n]` | Adresse MAC | regex |
| `[TEL_n]` | Téléphone FR | regex |
| `[CODE_POSTAL_n]` | CP FR | regex |
| `[IBAN_n]` | IBAN | MOD-97 |
| `[CB_n]` | Carte bancaire | Luhn |
| `[NIR_n]` | N° sécu FR | clé de contrôle |
| `[SIRET_n]` | SIRET (14 chiffres) | Luhn |
| `[SIREN_n]` | SIREN (9 chiffres, avec mot-clé) | Luhn |
| `[HOSTNAME_n]` | Hostname interne (`.lan`, `.local`, ...) | regex |
| `[PORT_n]` | Port réseau nommé | regex |
| `[DATE_NAISSANCE_n]` | Date de naissance (mot-clé : `né(e) le`, `DOB`, `born on`, …) | regex + proximité |
| `[PERSONNE_n]` / `[ORGANISATION_n]` / `[LIEU_n]` / `[DIVERS_n]` | NER spaCy | — |

## API HTTP

| Endpoint | Méthode | Effet |
|---|---|---|
| `/` | GET | Interface |
| `/status` | GET | État Tesseract / OCR |
| `/anonymize` | POST | Multipart : `file` + `mapping?` |
| `/deanonymize` | POST | Multipart : `file` + `mapping` + `password?` |
| `/download`, `/download-mapping`, `/download-mapping-encrypted` | POST | Génération fichier |
| `/categories` | GET / POST | Lecture / mise à jour catégories désactivées |
| `/ner-whitelist` | GET / POST | Lecture / mise à jour liste blanche (max 500 entrées, 200 chars/entrée) |
| `/set-tesseract` | POST | Configurer chemin Tesseract |
| `/admin/info`, `/admin/purge-logs`, `/admin/reset-config` | GET / POST | Administration (localhost ou `X-Admin-Key`) |

## Variables d'environnement

| Variable | Effet |
|---|---|
| `ANONYMISEUR_LOG_LEVEL` | `DEBUG` / `INFO` (défaut) / `WARNING` |
| `ANONYMISEUR_NO_BROWSER` | `1` pour ne pas ouvrir le navigateur au démarrage |
| `ANONYMISEUR_ADMIN_KEY` | Clé d'accès aux routes `/admin/*` depuis le réseau (intranet) |
| `ANONYMISEUR_CACHE_SIZE` | Taille du cache LRU `/anonymize` (défaut 32) |

## Page admin

Accessible via l'onglet *Admin* de l'interface.

- Consultation des 100 dernières lignes de log.
- Purge des logs.
- Réinitialisation de la configuration.

En déploiement intranet, l'accès admin est restreint au serveur lui-même (localhost) ou via l'en-tête `X-Admin-Key` si `ANONYMISEUR_ADMIN_KEY` est définie.

## Tests

```bat
python -m pytest
```

64 tests : validateurs (Luhn, IBAN, NIR, SIRET, SIREN), détection PII, dates de naissance, qualité NER (whitelist, min length), roundtrip dé-anonymisation, chiffrement. Coverage ~40 %.

CI déclenchée à chaque push/PR sur `main` (Ubuntu + Windows × Python 3.11 / 3.12).

## Build

```bat
build.bat              :: Anonymiseur.exe (PyInstaller)
build_installer.bat    :: Installeur Inno Setup (.exe) — génère installer\Output\Anonymiseur-Setup-1.2.0.exe
```

Pré-requis Tesseract embarqué : déposer Tesseract portable dans `vendor\tesseract\` avant `build.bat`.

Le bundle PyInstaller inclut :
- modèle spaCy `fr_core_news_md`,
- Tesseract portable (si présent),
- `templates/`, `static/` (CSS + 9 fichiers de polices).

## Conformité

- Traitement 100 % local (poste) ou intranet (serveur interne) — aucune télémétrie, aucune connexion sortante.
- Polices embarquées localement — aucun appel à Google Fonts ni CDN externe.
- Le `mapping.json` contient les valeurs originales — à traiter comme donnée sensible. Utiliser le chiffrement AES-256-GCM intégré pour le protéger par mot de passe avant tout stockage ou partage interne.

## Licence

Usage interne Action Telecom.
