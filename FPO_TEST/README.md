# 🔍 FPO_TEST - Script de Diagnostic

## Description

Script de diagnostic pour tester l'intégration de l'API Edilkamin.

## 🚀 Utilisation Rapide

### Option 1: Variables d'Environnement (Recommandé ✅)

#### 🐧 Bash (Linux/Mac)
```bash
export EDILKAMIN_USERNAME="your_email@example.com"
export EDILKAMIN_PASSWORD="your_password_here"
export EDILKAMIN_MAC="00:11:22:33:44:55"
python diagnostic_template.py
```

#### 🪟 PowerShell (Windows)
```powershell
$env:EDILKAMIN_USERNAME = "your_email@example.com"
$env:EDILKAMIN_PASSWORD = "your_password_here"
$env:EDILKAMIN_MAC = "00:11:22:33:44:55"

python diagnostic_template.py
```

#### 🪟 Variante PowerShell (une seule ligne)
```powershell
$env:EDILKAMIN_USERNAME = "your_email@example.com"; $env:EDILKAMIN_PASSWORD = "your_password_here"; $env:EDILKAMIN_MAC = "00:11:22:33:44:55"; python diagnostic_template.py
```

**Avantages**:
- ✅ Credentials jamais sauvegardés dans les fichiers
- ✅ Safe pour Git
- ✅ Recommandé pour production

### Option 2: Fichier .env.local

À la racine du projet (pas dans FPO_TEST):
```bash
echo "EDILKAMIN_USERNAME=your_email@example.com" > ../.env.local
echo "EDILKAMIN_PASSWORD=your_password_here" >> ../.env.local
echo "EDILKAMIN_MAC=00:11:22:33:44:55" >> ../.env.local

python diagnostic_template.py
```

Le script charge automatiquement `.env.local`

**Avantages**:
- ✅ Fichier .env.local est ignoré par Git (.gitignore)
- ✅ Configuration persistante
- ✅ Plus facile pour tests répétés

### Option 3: Éditer le Script

Éditez directement `diagnostic_template.py` et remplacez:
```python
USERNAME = "your_email@example.com"  # ← Mettre votre email
PASSWORD = "your_password_here"      # ← Mettre votre password
MAC_ADDRESS = "00:11:22:33:44:55"   # ← Mettre votre MAC
```

**Attention**: Ne pas committer après modification!

---

## 📊 Tests Effectués

Le script teste 4 aspects:

1. **SSL** - Vérification HTTPS vers l'API
2. **Authentification** - AWS Cognito
3. **Device Info** - Récupération données du poêle
4. **MQTT Check** - Test commande MQTT

---

## ✅ Résultats Attendus

```
TEST 1 : Connexion SSL
[+] Connexion SSL OK - Status: 403

TEST 2 : Authentification AWS Cognito
[+] Authentification OK

TEST 3 : Récupération des infos du dispositif
[+] Données valides reçues

TEST 4 : Commande MQTT 'check'
[-] Status 504

RESUME DES RESULTATS
SSL                  : [+] OK
Authentication       : [+] OK
Device Info          : [+] OK
MQTT Check           : [-] ERREUR
```

---

## ⚠️ Sécurité

**RÈGLES IMPORTANTES**:

1. ❌ **JAMAIS** committer vos credentials dans Git
2. ✅ **TOUJOURS** utiliser variables d'environnement ou `.env.local`
3. ✅ Le fichier `.env.local` est ignoré par Git (.gitignore)
4. ✅ Les credentials dans le terminal ne sont pas sauvegardés

---

## 📝 Dépendances

```bash
pip install pycognito httpx
```

Ces packages sont déjà dans `pyproject.toml`

---

**Status**: ✅ Production Ready
**Dernière mise à jour**: 2026-03-06

