#!/usr/bin/env python3
"""Verify the manifest.json file is valid and complete."""

import json
import sys
from pathlib import Path

def verify_manifest():
    """Verify manifest.json is correct."""
    manifest_path = Path(__file__).parent / "custom_components" / "edilkamin" / "manifest.json"

    print(f"🔍 Vérification du manifest: {manifest_path}")
    print("-" * 60)

    # Check file exists
    if not manifest_path.exists():
        print(f"❌ ERREUR: Le fichier manifest.json n'existe pas!")
        return False

    print(f"✅ Fichier trouvé: {manifest_path}")

    # Validate JSON
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        print("✅ JSON valide")
    except json.JSONDecodeError as e:
        print(f"❌ ERREUR JSON: {e}")
        return False

    # Check required fields
    required_fields = [
        "domain",
        "name",
        "codeowners",
        "config_flow",
        "documentation",
        "integration_type",
        "iot_class",
        "version",
    ]

    print("\n📋 Vérification des champs requis:")
    print("-" * 60)

    all_present = True
    for field in required_fields:
        if field in manifest:
            value = manifest[field]
            # Limit display of long values
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  ✅ {field}: {value}")
        else:
            print(f"  ❌ MANQUANT: {field}")
            all_present = False

    # Check optional but recommended fields
    print("\n📝 Champs optionnels (recommandés):")
    print("-" * 60)
    optional_fields = ["python_version", "requirements", "dependencies"]

    for field in optional_fields:
        if field in manifest:
            value = manifest[field]
            if isinstance(value, list):
                value = f"[{len(value)} item(s)]"
            elif isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  ✅ {field}: {value}")
        else:
            print(f"  ⚠️  Non défini: {field}")

    print("\n" + "=" * 60)
    if all_present:
        print("✅ Le manifest.json semble valide et complet!")
        return True
    else:
        print("❌ Certains champs requis sont manquants!")
        return False

if __name__ == "__main__":
    success = verify_manifest()
    sys.exit(0 if success else 1)

