#!/usr/bin/env python3
"""
Script d'exécution rapide pour peupler la base de données
=========================================================

Ce script configure l'environnement Django et exécute le script de population.

Usage:
    cd scolaris
    python scripts/run_populate.py
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

# Import et exécution
from scripts.populate_school_data import populate_all_data

if __name__ == "__main__":
    print("🎯 Exécution du script de population des données scolaires...")
    print()
    
    # Demander confirmation
    confirm = input("⚠️  Voulez-vous vraiment peupler la base de données ? (y/N): ")
    
    if confirm.lower() in ['y', 'yes', 'oui', 'o']:
        try:
            populate_all_data()
        except KeyboardInterrupt:
            print("\n❌ Script interrompu par l'utilisateur.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Erreur lors de l'exécution: {e}")
            sys.exit(1)
    else:
        print("❌ Opération annulée.")
        sys.exit(0)
