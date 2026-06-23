# Anonymiseur de données sensibles — Action Telecom

Outil d'anonymisation de textes, logs, PDF et images avant soumission à un service d'IA externe (ChatGPT, Claude, Mistral, etc.). Traitement 100 % local ou intranet — aucune donnée ne sort du SI.

**Version actuelle : 1.1.0**

## Fonctionnalités

- Détection regex : emails, IPv4/IPv6, MAC, téléphones FR, codes postaux, IBAN, CB, NIR, SIRET, SIREN, hostnames internes, ports.
- Validation algorithmique : Luhn (CB, SIRET, SIREN), MOD-97 (IBAN), clé de contrôle (NIR) — réduit fortement les faux positifs.
- NER spaCy FR : personnes, organisations, lieux.
- OCR Tesseract pour images et PDF scannés.
- Interface web (Flask) avec téléchargement du texte anonymisé et du mapping JSON pour dé-anonymisation.
- Chiffrement AES-256-GCM du mapping (protection du fichier de dé-anonymisation par mot de passe).
- Copie presse-papier en un clic du texte anonymisé.
- Page admin : consultation des logs, purge, réinitialisation de la configuration.
- Déploiement poste unique (installeur `.exe`) ou serveur intranet partagé.

## Public visé

Techniciens, commerciaux et administratifs d'Action Telecom qui doivent partager des extraits de logs, tickets ou échanges client avec un assistant IA sans divulguer de données sensibles.

## Installation poste utilisateur

### Option 1 — Installeur (recommandé)

1. Récupérer `Anonymiseur-Setup-1.1.0.exe` (généré par `build_installer.bat`).
2. Double-cliquer → suivant → terminer.
3. Lancer via le menu Démarrer : *Action Telecom → Anonymiseur*. Le navigateur s'ouvre automatiquement.

Tesseract est embarqué dans l'installeur. Rien d'autre à installer.

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
2. Cliquer *Anonymiser*.
3. Récupérer le texte anonymisé (bouton télécharger ou copier).
4. Optionnel : télécharger le `mapping.json` (clair ou chiffré avec mot de passe) pour pouvoir restaurer le texte original.
5. Pour restaurer : onglet *Dé-anonymiser*, fournir le texte anonymisé + le `mapping.json`.

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
| `[SIRET_n]` | SIRET (14 chiffres) | Luhn |
| `[SIREN_n]` | SIREN (9 chiffres, avec mot-clé) | Luhn |
| `[HOSTNAME_n]` | Hostname interne (`.lan`, `.local`, ...) | regex |
| `[PORT_n]` | Port réseau nommé | regex |
| `[PERSONNE_n]` / `[ORGANISATION_n]` / `[LIEU_n]` | NER spaCy | — |

## Variables d'environnement

| Variable | Effet |
|---|---|
| `ANONYMISEUR_LOG_LEVEL` | `DEBUG` / `INFO` (défaut) / `WARNING` |
| `ANONYMISEUR_NO_BROWSER` | `1` pour ne pas ouvrir le navigateur au démarrage |
| `ANONYMISEUR_ADMIN_KEY` | Clé d'accès aux routes `/admin/*` depuis le réseau (intranet) |

## Page admin

Accessible via le bouton *Admin* de l'interface (ou `http://127.0.0.1:7777/admin`).

- Consultation des 100 dernières lignes de log.
- Purge des logs.
- Réinitialisation de la configuration.

En déploiement intranet, l'accès admin est restreint au serveur lui-même (localhost) ou via l'en-tête `X-Admin-Key` si `ANONYMISEUR_ADMIN_KEY` est définie.

## Tests

```bat
python -m pytest
```

27 tests : validateurs (Luhn, IBAN, NIR, SIRET, SIREN) + détection + roundtrip dé-anonymisation.

## Build

```bat
build.bat              :: Anonymiseur.exe (PyInstaller)
build_installer.bat    :: Installeur Inno Setup (.exe) — génère installer\Output\Anonymiseur-Setup-1.1.0.exe
```

Pré-requis Tesseract embarqué : déposer Tesseract portable dans `vendor\tesseract\` avant `build.bat`.

## Conformité

- Traitement 100 % local (poste) ou intranet (serveur interne) — aucune télémétrie, aucune connexion sortante.
- Le `mapping.json` contient les valeurs originales — à traiter comme donnée sensible. Utiliser le chiffrement AES-256-GCM intégré pour le protéger par mot de passe avant tout stockage ou partage interne.

## Licence

Usage interne Action Telecom.
