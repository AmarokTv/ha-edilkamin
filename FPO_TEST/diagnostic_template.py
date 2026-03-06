#!/usr/bin/env python3
"""
Script de diagnostic complet pour l'API Edilkamin
Teste tous les aspects pour identifier où est le problème

IMPORTANT: Configure tes credentials avant d'utiliser ce script!

USAGE:
    1. Édite ce fichier et remplace USERNAME, PASSWORD et MAC_ADDRESS
    2. Ou utilise des variables d'environnement:
       - EDILKAMIN_USERNAME=ton_email@example.com
       - EDILKAMIN_PASSWORD=ton_mot_de_passe
       - EDILKAMIN_MAC=00:11:22:33:44:55
    3. Lance le script: python diagnostic_template.py

TESTS EFFECTUES:
    ✓ TEST 1: Connexion SSL à l'API
    ✓ TEST 2: Authentification AWS Cognito
    ✓ TEST 3: Récupération des infos du dispositif
    ✓ TEST 4: Commande MQTT 'check'
    ✓ TEST 5: Changement de température (optionnel - demande confirmation)

ATTENTION:
    - Le TEST 5 va REELLEMENT changer la température de ton poêle!
    - Le script te demandera de confirmer avant de l'exécuter
    - Ne partage jamais ce script avec tes credentials réels dans le code
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
        print(f"Payload: {payload}\n")

        start_time = time.time()
        response = httpx.put(url, json=payload, headers=headers, verify=False, timeout=60.0)
        elapsed = time.time() - start_time

        print(f"Reponse recue en {elapsed:.2f}s")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print(f"\n[+] Commande executee avec succes")
            return True
        else:
            print(f"\n[-] Status {response.status_code}")
            return False

    except Exception as e:
        print(f"[-] Erreur: {e}")
        return False


def test_mqtt_set_temperature(token, temperature=20.0):
    """Test la commande MQTT 'enviroment_1_temperature'"""
    print_header(f"TEST 5 : Commande MQTT 'enviroment_1_temperature' (set {temperature}°C)")

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "mac_address": MAC_ADDRESS.replace(":", "").lower(),
            "name": "enviroment_1_temperature",
            "value": temperature
        }

        url = "https://the-mind-api.edilkamin.com/mqtt/command"

        print(f"Changement de temperature a {temperature}°C...")
        print(f"\nDetails de la requete HTTP:")
        print(f"  URL: {url}")
        print(f"  Methode: PUT")
        print(f"  Headers:")
        print(f"    - Authorization: Bearer {token[:30]}...")
        print(f"    - Content-Type: application/json")
        print(f"  Payload: {payload}")
        print(f"  Timeout: 60s\n")

        start_time = time.time()
        response = httpx.put(url, json=payload, headers=headers, verify=False, timeout=60.0)
        elapsed = time.time() - start_time

        print(f"Reponse recue en {elapsed:.2f}s")
        print(f"\nDetails de la reponse:")
        print(f"  Status HTTP: {response.status_code}")
        print(f"  Headers reponse:")
        for key, value in response.headers.items():
            if key.lower() not in ['set-cookie', 'authorization']:
                print(f"    - {key}: {value}")
        print(f"\nBody reponse:")
        print(f"  {response.text}")

        if response.status_code == 200:
            print(f"\n✅ [+] Temperature changee avec succes!")
            try:
                print(f"Response JSON: {response.json()}")
            except:
                pass
            return True
        elif response.status_code == 504:
            print(f"\n❌ [-] ERREUR 504 (Bad Gateway)")
            print(f"\nCette erreur signifie que le serveur Edilkamin rejette la requete.")
            print(f"\nPossibles raisons:")
            print(f"  1. Le poele est peut-etre en mode qui refuse les changements (Standby/Chrono/Cooling)")
            print(f"  2. Conflits de commandes ou limite de taux d'appels")
            print(f"  3. Probleme de synchronisation entre Home Assistant et le poele")
            print(f"  4. Token d'authentification expire ou invalide")
            print(f"  5. Adresse MAC invalide ou incorrecte")
            print(f"\nPROCHAINE ETAPE: Verifiez les infos du TEST 3 (Device Info)")
            print(f"  - L'etat du poele doit etre 'On' (2), pas 'Cooling' (4) ou autre")
            print(f"  - Verifiez que la valeur actuelle de enviroment_1_temperature est valide")
            print(f"  - Allez dans Home Assistant et reessayez manuellement")
            return False
        elif response.status_code == 401:
            print(f"\n❌ [-] ERREUR 401 (Unauthorized)")
            print(f"Le token d'authentification est invalide ou expire.")
            print(f"Redemarre le test.")
            return False
        elif response.status_code in [400, 422]:
            print(f"\n❌ [-] ERREUR {response.status_code} (Bad Request)")
            print(f"Le payload est invalide. Verifiez:")
            print(f"  - La temperature est entre 10 et 30°C")
            print(f"  - L'adresse MAC est correcte")
            print(f"  - Le nom de la commande 'enviroment_1_temperature' est exact")
            return False
        else:
            print(f"\n⚠️  [-] Status HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except httpx.TimeoutException as e:
        print(f"❌ [-] TIMEOUT apres 60s: {e}")
        print(f"Le serveur Edilkamin ne repond pas assez vite.")
        return False
    except Exception as e:
        print(f"❌ [-] Erreur: {e}")
        import traceback
        traceback.print_exc()
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
        "MQTT Set Temperature": False,
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

        # Test de changement de température
        # ⚠️  ATTENTION: Ceci va REELLEMENT changer la température du poele!
        print("\n" + "=" * 70)
        print("[!] ATTENTION: Le test suivant va REELLEMENT changer la temperature du poele!")
        print("=" * 70)

        # Vérifier l'état du poêle avant de tenter le changement
        print("\n🔍 VERIFICATION DE L'ETAT DU POELE:")
        print("=" * 70)

        try:
            device_data = None
            headers = {"Authorization": f"Bearer {id_token}"}
            mac_clean = MAC_ADDRESS.replace(":", "").lower()
            url = f"https://the-mind-api.edilkamin.com/device/{mac_clean}/info"

            response = httpx.get(url, headers=headers, verify=False, timeout=60.0)
            if response.status_code == 200:
                device_data = response.json()

                if "status" in device_data:
                    status = device_data["status"]

                    # Vérifier l'alimentation
                    is_power_on = status.get("commands", {}).get("power", 0)
                    stove_state_code = status.get("state", {}).get("stove_state", -1)

                    # Mapping des états du poêle
                    OPERATIONAL_STATES = {
                        0: "Off",
                        1: "Ignition",
                        2: "On",
                        3: "Shutdown",
                        4: "Cooling",
                        5: "Alarm",
                        6: "Final cleaning",
                        7: "Unknown",
                    }
                    stove_state_name = OPERATIONAL_STATES.get(stove_state_code, "INCONNU")

                    print(f"\n✓ Etat du poele (detaille):")
                    print(f"  - Alimentation: {'✅ ON' if is_power_on else '❌ OFF'} (power={is_power_on})")
                    print(f"  - Etat operationnel: {stove_state_name} (code={stove_state_code})")

                    # Afficher TOUS les modes et états
                    print(f"\n  Modes:")
                    commands = status.get("commands", {})
                    print(f"    - Auto mode: {commands.get('auto_mode', 'N/A')}")
                    print(f"    - Chrono mode: {commands.get('chrono_mode', 'N/A')}")
                    print(f"    - Standby mode: {commands.get('standby_mode', 'N/A')}")
                    print(f"    - Relax mode: {commands.get('relax_mode', 'N/A')}")
                    print(f"    - Airkare function: {commands.get('airkare_function', 'N/A')}")

                    print(f"\n  Temperatures:")
                    user_params = device_data.get("nvm", {}).get("user_parameters", {})
                    temps = status.get("temperatures", {})
                    print(f"    - Cible env 1: {user_params.get('enviroment_1_temperature', 'N/A')}°C")
                    print(f"    - Cible env 2: {user_params.get('enviroment_2_temperature', 'N/A')}°C")
                    print(f"    - Actuelle env: {temps.get('enviroment', 'N/A')}°C")
                    print(f"    - Thermocouple: {temps.get('thermocouple', 'N/A')}°C")

                    print(f"\n  Autres infos:")
                    print(f"    - Puissance actuelle: {status.get('state', {}).get('actual_power', 'N/A')}%")
                    print(f"    - Alarm reset: {commands.get('alarm_reset', 'N/A')}")

                    # Vérifier les conditions pour accepter un changement de température
                    print(f"\n📋 Conditions pour changer la temperature:")

                    conditions_ok = True

                    if not is_power_on:
                        print(f"  ❌ Le poele doit etre ALLUME (power=1)")
                        conditions_ok = False
                    else:
                        print(f"  ✅ Poele allume")

                    if stove_state_code == 5:  # Alarm
                        print(f"  ❌ Le poele est en ALARME! Impossible de changer la temperature")
                        conditions_ok = False
                    elif stove_state_code not in [1, 2, 4]:  # Ignition, On, Cooling
                        print(f"  ⚠️  L'etat '{stove_state_name}' peut ne pas accepter les changements")
                    else:
                        print(f"  ✅ L'etat operationnel est compatible")

                    if stove_state_code == 3:  # Shutdown
                        print(f"  ❌ Le poele est en ARRÊT (Shutdown)")
                        conditions_ok = False

                    if conditions_ok:

                        response = input("\nVeux-tu continuer? (oui/non): ").strip().lower()

                        if response in ["oui", "yes", "y", "o"]:
                            # Demander la température souhaitée
                            try:
                                temp_input = input("\nQuelle temperature veux-tu definir? (defaut: 20°C): ").strip()
                                temp_value = float(temp_input) if temp_input else 20.0

                                # Valider la plage de température
                                if temp_value < 10 or temp_value > 30:
                                    print(f"[-] Temperature invalide! Doit etre entre 10 et 30°C")
                                else:
                                    results["MQTT Set Temperature"] = test_mqtt_set_temperature(id_token, temp_value)
                            except ValueError:
                                print(f"[-] Valeur invalide, utilisation de la temperature par defaut 20°C")
                                results["MQTT Set Temperature"] = test_mqtt_set_temperature(id_token, 20.0)
                        else:
                            print("\nTest de changement de temperature saute.")
                else:
                    print("❌ Impossible de recuperer l'etat du poele")
                    results["MQTT Set Temperature"] = False
            else:
                print(f"❌ Erreur lors de la recuperation des infos du poele: {response.status_code}")
                results["MQTT Set Temperature"] = False

        except Exception as e:
            print(f"❌ Erreur lors de la verification: {e}")
            results["MQTT Set Temperature"] = False

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
        print(f"{test_name:30} : {status}")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

