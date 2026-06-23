# Anonymiseur de données sensibles — Action Telecom

Outil local d'anonymisation de textes, logs, PDF et images avant soumission à un service d'IA externe (ChatGPT, Claude, Mistral, etc.). Aucune donnée ne sort du poste.

## Fonctionnalités

- Détection regex : emails, IPv4/IPv6, MAC, téléphones FR, codes postaux, IBAN, CB, NIR, hostnames internes, ports.
- Validation : Luhn (CB), MOD-97 (IBAN), clé de contrôle (NIR) — réduit fortement les faux positifs.
- NER spaCy FR : personnes, organisations, lieux.
- OCR Tesseract pour images et PDF scannés.
- Interface web locale (Flask) avec téléchargement du texte anonymisé et du mapping JSON pour dé-anonymisation.
- Exécution 100 % locale, port `127.0.0.1` uniquement.

## Public visé

Techniciens, commerciaux et administratifs d'Action Telecom qui doivent partager des extraits de logs, tickets ou échanges client avec un assistant IA sans divulguer de données sensibles.

## Installation poste utilisateur

### Option A — Installeur (recommandé)

1. Récupérer `Anonymiseur-Setup-1.0.0.exe` (généré par `build_installer.bat`).
2. Double-cliquer → suivant → terminer.
3. Lancer via le menu Démarrer : *Action Telecom → Anonymiseur*. Le navigateur s'ouvre automatiquement.

Tesseract est embarqué dans l'installeur. Rien d'autre à installer.

### Option B — Lancement depuis les sources (dev)

```bat
install.bat       :: dépendances Python + modèle spaCy + tests
python app.py     :: lance l'interface web
```

Ouvre `http://127.0.0.1:7777` (ou un port libre si 7777 occupé).

## Utilisation

1. Glisser un fichier (`.txt`, `.log`, `.pdf`, `.png`, `.jpg`, ...).
2. Cliquer *Anonymiser*.
3. Récupérer le texte anonymisé et le `mapping.json`.
4. Pour restaurer : onglet *Dé-anonymiser*, fournir le texte anonymisé + le `mapping.json`.

## Emplacements de fichiers

| Quoi | Où |
|---|---|
| Config (chemin Tesseract manuel) | `%APPDATA%\ActionTelecom\Anonymiseur\config.json` |
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
| `[HOSTNAME_n]` | Hostname interne (`.lan`, `.local`, ...) | regex |
| `[PORT_n]` | Port réseau nommé | regex |
| `[PERSONNE_n]` / `[ORGANISATION_n]` / `[LIEU_n]` | NER spaCy | — |

## Variables d'environnement

| Variable | Effet |
|---|---|
| `ANONYMISEUR_LOG_LEVEL` | `DEBUG` / `INFO` (défaut) / `WARNING` |
| `ANONYMISEUR_NO_BROWSER` | `1` pour ne pas ouvrir le navigateur au démarrage |

## Tests

```bat
python -m pytest
```

22 tests : validateurs + détection + roundtrip dé-anonymisation.

## Build

```bat
build.bat              :: Anonymiseur.exe (PyInstaller)
build_installer.bat    :: Installeur Inno Setup (.exe)
```

Pré-requis Tesseract embarqué : déposer Tesseract portable dans `vendor\tesseract\` avant `build.bat`.

## Conformité

- 100 % traitement local, aucune télémétrie, aucune connexion sortante.
- Le `mapping.json` contient les valeurs originales — à traiter comme donnée sensible (ne pas le partager, le stocker dans un emplacement sécurisé).

## Licence

Usage interne Action Telecom.
