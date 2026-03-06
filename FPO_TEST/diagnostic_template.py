#!/usr/bin/env python3
"""
Script de diagnostic complet pour l'API Edilkamin
Teste tous les aspects pour identifier où est le problème

IMPORTANT: Configure tes credentials avant d'utiliser ce script!
"""

import sys
import warnings
import os
import time

# Désactiver tous les avertissements
warnings.filterwarnings('ignore')

# Désactiver la vérification SSL
os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["AWS_CA_BUNDLE"] = ""

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import ssl
_orig_ctx = ssl.create_default_context
def _no_verify_ctx(*args, **kwargs):
    ctx = _orig_ctx(*args, **kwargs)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
ssl.create_default_context = _no_verify_ctx

# Importer les dépendances
from pycognito import Cognito
from edilkamin import constants
import httpx

# ============================================================================
# ⚠️  CONFIGURATION - À REMPLIR AVEC TES DONNÉES
# ============================================================================
# ATTENTION: Ne jamais committer ces informations dans Git!
# Crée un fichier .env ou config_local.py pour tes credentials
# ============================================================================

USERNAME = "your_email@example.com"  # ← À REMPLACER par ton email
PASSWORD = "your_password_here"      # ← À REMPLACER par ton mot de passe
MAC_ADDRESS = "00:00:00:00:00:00"    # ← À REMPLACER par l'adresse MAC de ton poêle

# Alternative: Charger depuis variables d'environnement
import os as _os_env
USERNAME = _os_env.getenv("EDILKAMIN_USERNAME", USERNAME)
PASSWORD = _os_env.getenv("EDILKAMIN_PASSWORD", PASSWORD)
MAC_ADDRESS = _os_env.getenv("EDILKAMIN_MAC", MAC_ADDRESS)

# ============================================================================

def print_header(title):
    """Afficher un titre formaté"""
    print("\n" + "=" * 70)
    print(f"[*] {title}")
    print("=" * 70)


def test_ssl_connection():
    """Test la connexion SSL"""
    print_header("TEST 1 : Connexion SSL")

    try:
        print(f"Méthode: GET")
        response = httpx.get("https://the-mind-api.edilkamin.com/", verify=False, timeout=10.0)
        print(f"[+] Connexion SSL OK - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"[-] Erreur SSL: {e}")
        return False


def test_authentication():
    """Test l'authentification Cognito"""
    print_header("TEST 2 : Authentification AWS Cognito")

    try:
        print(f"Authentification de {USERNAME}...")
        cognito = Cognito(constants.USER_POOL_ID, constants.CLIENT_ID, username=USERNAME)
        cognito.authenticate(PASSWORD)
        user = cognito.get_user()
        id_token = user._metadata["id_token"]
        access_token = user._metadata["access_token"]

        print(f"[+] Authentification OK")
        print(f"ID Token: {id_token[:50]}...")
        print(f"Access Token: {access_token[:50]}...")
        return (id_token, access_token)
    except Exception as e:
        print(f"[-] Erreur authentification: {e}")
        return (None, None)


def test_device_info(token):
    """Test la récupération des infos du dispositif"""
    print_header("TEST 3 : Récupération des infos du dispositif")

    try:
        headers = {
            "Authorization": f"Bearer {token}",
        }

        mac_clean = MAC_ADDRESS.replace(":", "").lower()
        url = f"https://the-mind-api.edilkamin.com/device/{mac_clean}/info"

        print(f"Méthode: GET")
        print(f"URL: {url}")
        print(f"Timeout: 60 secondes")
        print(f"Envoi de la requête...")

        start_time = time.time()
        response = httpx.get(url, headers=headers, verify=False, timeout=60.0)
        elapsed = time.time() - start_time

        print(f"[+] Réponse reçue en {elapsed:.2f}s")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[+] Données valides reçues")

            # Structure des données
            print(f"\nSTRUCTURE DES DONNEES RECUES:")
            print(f"\n1. INFORMATIONS COMPOSANTS (component_info):")
            if "component_info" in data:
                comp = data["component_info"]
                print(f"   - Timestamp: {comp.get('timestamp', 'N/A')}")
                if "motherboard" in comp:
                    mb = comp["motherboard"]
                    print(f"   - Carte mere: {mb.get('board_name', 'N/A')}")
                    print(f"   - Version app: {mb.get('application_version', 'N/A')}")

            print(f"\n2. ETAT EN TEMPS REEL (status):")
            if "status" in data:
                status = data["status"]
                print(f"   - Etat du poele: {status['state']['stove_state']}")
                print(f"   - Puissance actuelle: {status['state']['actual_power']}")
                print(f"   - Alimentation: {'ON' if status['commands']['power'] else 'OFF'}")

                print(f"\n   Temperatures:")
                temps = status.get("temperatures", {})
                print(f"      - Ambiante (enviroment): {temps.get('enviroment', 'N/A')}C")
                print(f"      - Thermocouple: {temps.get('thermocouple', 'N/A')}C")
                print(f"      - Carte electronique: {temps.get('board', 'N/A')}C")
                print(f"      - Capteur 1 (NTC 1): {temps.get('feeler_ntc_1', 'N/A')}C")

                print(f"\n   Ventilateurs:")
                fans = status.get("fans", {})
                print(f"      - Ventilateur 1: {fans.get('fan_1_speed', 'N/A')}%")
                print(f"      - Ventilateur 2: {fans.get('fan_2_speed', 'N/A')}%")
                print(f"      - Ventilateur 3: {fans.get('fan_3_speed', 'N/A')}%")

            print(f"\n3. PARAMETRES UTILISATEUR (nvm.user_parameters):")
            if "nvm" in data and "user_parameters" in data["nvm"]:
                user_params = data["nvm"]["user_parameters"]
                print(f"   - Temperature cible env 1: {user_params.get('enviroment_1_temperature', 'N/A')}C")

            return True
        else:
            print(f"[-] Status {response.status_code}")
            return False

    except httpx.TimeoutException as e:
        print(f"[-] TIMEOUT apres 60s: {e}")
        return False
    except Exception as e:
        print(f"[-] Erreur: {e}")
        return False


def test_mqtt_check_command(token):
    """Test la commande MQTT 'check'"""
    print_header("TEST 4 : Commande MQTT 'check'")

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "mac_address": MAC_ADDRESS.replace(":", "").lower(),
            "name": "check"
        }

        url = "https://the-mind-api.edilkamin.com/mqtt/command"

        print(f"Envoi de la requete...")

        start_time = time.time()
        response = httpx.put(url, json=payload, headers=headers, verify=False, timeout=60.0)
        elapsed = time.time() - start_time

        print(f"Reponse recue en {elapsed:.2f}s")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print(f"[+] Commande executee")
            return True
        else:
            print(f"[-] Status {response.status_code}")
            return False

    except Exception as e:
        print(f"[-] Erreur: {e}")
        return False


def main():
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLET API EDILKAMIN")
    print("=" * 70)
    print("\nAVERTISSEMENT: Configures USERNAME, PASSWORD et MAC_ADDRESS avant de lancer!")
    print("Ne commit jamais ce fichier avec des credentials reels!")
    print("Utilise plutot des variables d'environnement ou un fichier .env")

    if USERNAME == "your_email@example.com":
        print("\n[!] ERREUR: Tu dois configurer tes credentials!")
        print("    - USERNAME: remplace par ton email Edilkamin")
        print("    - PASSWORD: remplace par ton mot de passe")
        print("    - MAC_ADDRESS: remplace par l'adresse MAC de ton poele")
        return

    results = {
        "SSL": False,
        "Authentication": False,
        "Device Info": False,
        "MQTT Check": False,
    }

    try:
        results["SSL"] = test_ssl_connection()
        if not results["SSL"]:
            print("\n[-] La connexion SSL echoue, impossible de continuer")
            return

        id_token, access_token = test_authentication()
        results["Authentication"] = id_token is not None and access_token is not None

        if not id_token or not access_token:
            print("\n[-] L'authentification echoue, impossible de continuer")
            return

        results["Device Info"] = test_device_info(id_token)
        results["MQTT Check"] = test_mqtt_check_command(id_token)

    except KeyboardInterrupt:
        print("\n\n[-] Test interrompu par l'utilisateur")
        return
    except Exception as e:
        print(f"\n\n[-] Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return

    # Résumé final
    print_header("RESUME DES RESULTATS")

    for test_name, result in results.items():
        status = "[+] OK" if result else "[-] ERREUR"
        print(f"{test_name:20} : {status}")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

