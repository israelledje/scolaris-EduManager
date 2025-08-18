#!/usr/bin/env python
"""
Script de migration simple de SQLite vers PostgreSQL
Utilise les commandes Django standard
"""

import os
import sys
import django
import subprocess
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

def run_command(command):
    """Exécute une commande Django"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur avec {command}: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False

def backup_sqlite():
    """Sauvegarde la base SQLite"""
    print("🔄 Sauvegarde de la base SQLite...")
    
    import shutil
    
    backup_dir = 'backup_sqlite'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{backup_dir}/db_backup_{timestamp}.sqlite3"
    
    shutil.copy2('db.sqlite3', backup_file)
    print(f"✅ Sauvegarde créée : {backup_file}")
    return backup_file

def main():
    """Migration principale"""
    print("=" * 60)
    print("🚀 MIGRATION SIMPLE SQLITE → POSTGRESQL")
    print("=" * 60)
    
    # Sauvegarde
    backup_file = backup_sqlite()
    
    print("\n📋 Étapes de migration :")
    print("1. Créer les migrations")
    print("2. Appliquer les migrations")
    print("3. Exporter les données SQLite")
    print("4. Importer dans PostgreSQL")
    
    # Étape 1: Créer les migrations
    print("\n1️⃣ Création des migrations...")
    if not run_command("python manage.py makemigrations"):
        print("❌ Échec de la création des migrations")
        return
    
    # Étape 2: Appliquer les migrations
    print("\n2️⃣ Application des migrations...")
    if not run_command("python manage.py migrate"):
        print("❌ Échec de l'application des migrations")
        return
    
    # Étape 3: Exporter les données
    print("\n3️⃣ Export des données SQLite...")
    if not run_command("python manage.py dumpdata --exclude contenttypes --exclude auth.Permission --indent 2 -o temp_data.json"):
        print("❌ Échec de l'export des données")
        return
    
    # Étape 4: Importer dans PostgreSQL
    print("\n4️⃣ Import dans PostgreSQL...")
    if not run_command("python manage.py loaddata temp_data.json"):
        print("❌ Échec de l'import des données")
        return
    
    # Nettoyage
    if os.path.exists('temp_data.json'):
        os.remove('temp_data.json')
        print("🧹 Fichier temporaire supprimé")
    
    print("\n" + "=" * 60)
    print("🎉 MIGRATION TERMINÉE !")
    print("=" * 60)
    print(f"📁 Sauvegarde : {backup_file}")
    print("💡 Vous pouvez maintenant supprimer db.sqlite3")
    print("💡 Redémarrez votre serveur Django")

if __name__ == '__main__':
    main()
