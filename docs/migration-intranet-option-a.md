# Migration SafePrompt — Hébergement intranet (Option A)

**Cible :** Serveur Windows intranet Action Telecom  
**Accès utilisateur :** `http://<IP-SERVEUR>:7777` depuis n'importe quel poste du réseau  
**Pré-requis réseau :** Accès LAN au serveur sur le port 7777  

---

## 1. Pré-requis serveur

| Composant | Version minimale | Notes |
|---|---|---|
| Windows Server | 2019 ou 2022 | Ou poste Windows 10/11 dédié |
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Tesseract OCR | 5.x | Requis pour OCR images/PDF scannés |
| NSSM | 2.24+ | Pour exécuter en service Windows |
| Git | Optionnel | Pour mise à jour depuis GitHub |

---

## 2. Installation du projet sur le serveur

### 2.1 Copier les sources

```bat
:: Option A — Depuis GitHub (recommandé)
git clone https://github.com/Neo-code769/SafePrompt.git C:\SafePrompt

:: Option B — Copie manuelle
:: Copier le dossier du projet vers C:\SafePrompt
```

### 2.2 Installer les dépendances Python

```bat
cd C:\SafePrompt
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m spacy download fr_core_news_md
```

### 2.3 Installer Tesseract

1. Télécharger l'installeur depuis : https://github.com/UB-Mannheim/tesseract/wiki
2. Installer dans `C:\Program Files\Tesseract-OCR\`
3. Ajouter au PATH système : `C:\Program Files\Tesseract-OCR\`
4. Vérifier : `tesseract --version`

---

## 3. Configuration de l'application

### 3.1 Modifier la liaison réseau

Éditer `C:\SafePrompt\app.py`, ligne contenant `app.run(...)` :

```python
# AVANT (local uniquement)
app.run(debug=False, host="127.0.0.1", port=port, use_reloader=False)

# APRÈS (accessible sur le réseau intranet)
app.run(debug=False, host="0.0.0.0", port=port, use_reloader=False)
```

### 3.2 Désactiver l'ouverture automatique du navigateur

L'ouverture du navigateur au démarrage doit être désactivée (le serveur n'a pas de bureau utilisateur).

```bat
:: Définir la variable d'environnement au niveau système
setx ANONYMISEUR_NO_BROWSER 1 /M
```

### 3.3 Variables d'environnement recommandées

Définir via `setx ... /M` (niveau machine) ou dans les propriétés système :

| Variable | Valeur | Effet |
|---|---|---|
| `ANONYMISEUR_NO_BROWSER` | `1` | Désactive l'ouverture du navigateur |
| `ANONYMISEUR_LOG_LEVEL` | `INFO` | Niveau de log (DEBUG / INFO / WARNING) |
| `ANONYMISEUR_ADMIN_KEY` | `<clé-secrète>` | Clé d'accès à `/admin/*` depuis le réseau |

**Générer une clé admin :**
```bat
python -c "import secrets; print(secrets.token_hex(32))"
```

> **Important :** Conserver cette clé dans un endroit sécurisé. Elle permet d'accéder aux logs et à la configuration de l'application depuis n'importe quel poste du réseau.

---

## 4. Pare-feu Windows

Ouvrir le port 7777 en entrée sur le serveur :

```bat
:: En tant qu'administrateur
netsh advfirewall firewall add rule ^
  name="SafePrompt - Anonymiseur AT" ^
  dir=in action=allow protocol=TCP localport=7777 ^
  profile=domain,private
```

Vérifier la règle :
```bat
netsh advfirewall firewall show rule name="SafePrompt - Anonymiseur AT"
```

---

## 5. Installation en tant que service Windows (NSSM)

NSSM permet de démarrer l'application automatiquement avec Windows, sans session utilisateur ouverte.

### 5.1 Télécharger NSSM

```bat
winget install NSSM.NSSM
:: ou télécharger depuis https://nssm.cc/download
```

### 5.2 Installer le service

```bat
:: En tant qu'administrateur
nssm install SafePrompt "C:\Python311\python.exe" "C:\SafePrompt\app.py"
nssm set SafePrompt AppDirectory "C:\SafePrompt"
nssm set SafePrompt DisplayName "SafePrompt — Anonymiseur Action Telecom"
nssm set SafePrompt Description "Interface web locale d'anonymisation de donnees sensibles"
nssm set SafePrompt Start SERVICE_AUTO_START
nssm set SafePrompt AppStdout "C:\SafePrompt\logs\nssm-stdout.log"
nssm set SafePrompt AppStderr "C:\SafePrompt\logs\nssm-stderr.log"
nssm set SafePrompt AppEnvironmentExtra ^
  ANONYMISEUR_NO_BROWSER=1 ^
  ANONYMISEUR_LOG_LEVEL=INFO ^
  ANONYMISEUR_ADMIN_KEY=<remplacer-par-la-cle-generee>
```

> Remplacer `C:\Python311\python.exe` par le chemin réel de Python (`where python` pour le trouver).

### 5.3 Démarrer le service

```bat
nssm start SafePrompt
:: Vérifier le statut
nssm status SafePrompt
```

### 5.4 Commandes utiles

```bat
nssm start SafePrompt      :: Démarrer
nssm stop SafePrompt       :: Arrêter
nssm restart SafePrompt    :: Redémarrer
nssm remove SafePrompt     :: Désinstaller le service
```

---

## 6. Vérification du déploiement

### 6.1 Depuis le serveur

```bat
:: Vérifier que le port est en écoute
netstat -ano | findstr :7777

:: Test HTTP depuis le serveur
curl http://127.0.0.1:7777/status
```

Réponse attendue :
```json
{"ocr_available": true, "ocr_status": "...", "tesseract_path": "..."}
```

### 6.2 Depuis un poste client

Ouvrir un navigateur et accéder à :
```
http://<IP-DU-SERVEUR>:7777
```

Remplacer `<IP-DU-SERVEUR>` par l'IP ou le nom DNS du serveur (ex : `http://srv-at-tools:7777`).

### 6.3 Vérifier l'accès admin (optionnel)

```bat
:: Depuis un poste distant, avec la clé admin
curl -H "X-Admin-Key: <cle-admin>" http://<IP-SERVEUR>:7777/admin/info
```

---

## 7. Communication aux collaborateurs

Envoyer un message interne avec les informations suivantes :

```
Bonjour,

L'outil SafePrompt est désormais disponible sur l'intranet Action Telecom.

Accès : http://<IP-DU-SERVEUR>:7777
        (ou http://<NOM-DNS>:7777)

Fonctionnement :
- Collez ou déposez un texte / fichier contenant des données sensibles.
- L'outil remplace automatiquement les données (emails, IP, noms, IBAN...)
  par des marqueurs anonymes [EMAIL_1], [IPv4_1], etc.
- Téléchargez le texte anonymisé à transmettre à l'IA.
- Conservez le fichier mapping.json pour restaurer le texte original si besoin.

Aucune donnée ne quitte le réseau intranet.
```

---

## 8. Limitations de l'Option A

| Limitation | Impact | Mitigation |
|---|---|---|
| Pas de HTTPS | Trafic en clair sur le réseau LAN | Acceptable en réseau interne privé ; ajouter un reverse proxy Nginx avec certificat pour sécuriser |
| Pas d'authentification utilisateur | Tous les postes du réseau accèdent à l'outil | Filtrer par VLAN ou règle pare-feu si besoin de restriction |
| Logs partagés | Tous les traitements dans un seul fichier log | Acceptable — pas de données sensibles dans les logs (seul le nom de fichier est loggé) |
| Page admin accessible depuis réseau | Requiert la clé `ANONYMISEUR_ADMIN_KEY` | Définie à l'étape 3.3 |
| Pas de haute disponibilité | Si le serveur redémarre, service indisponible quelques secondes | NSSM redémarre automatiquement |

---

## 9. Mise à jour de l'application

```bat
:: Depuis le serveur, en tant qu'administrateur
nssm stop SafePrompt
cd C:\SafePrompt
git pull origin main
python -m pip install -r requirements.txt --upgrade
nssm start SafePrompt
```

---

## 10. Désinstallation

```bat
nssm stop SafePrompt
nssm remove SafePrompt confirm
netsh advfirewall firewall delete rule name="SafePrompt - Anonymiseur AT"
rmdir /s /q C:\SafePrompt
```

Les logs et la configuration utilisateur (dans `%APPDATA%\ActionTelecom\`) ne sont pas supprimés automatiquement.
