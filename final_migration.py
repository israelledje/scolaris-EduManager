#!/usr/bin/env python
"""
Script final de migration SQLite → PostgreSQL
Gère le basculement entre les bases de données
"""

import os
import sys
import django
import json
import shutil
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.conf import settings
from django.core.management import execute_from_command_line

def backup_sqlite():
    """Sauvegarde la base SQLite"""
    print("🔄 Sauvegarde de la base SQLite...")
    
    backup_dir = 'backup_sqlite'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{backup_dir}/db_backup_{timestamp}.sqlite3"
    
    shutil.copy2('db.sqlite3', backup_file)
    print(f"✅ Sauvegarde créée : {backup_file}")
    return backup_file

def export_from_sqlite():
    """Exporte les données depuis SQLite"""
    print("💾 Export des données depuis SQLite...")
    
    # Sauvegarder la configuration PostgreSQL actuelle
    original_db = settings.DATABASES['default'].copy()
    
    try:
        # Basculer temporairement vers SQLite
        settings.DATABASES['default'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite3',
        }
        
        # Forcer le rechargement des connexions
        from django.db import connections
        connections.close_all()
        
        # Exporter les données
        execute_from_command_line(['manage.py', 'dumpdata', '--exclude', 'contenttypes', '--exclude', 'auth.Permission', '--indent', '2', '-o', 'temp_data.json'])
        
        print("✅ Données exportées depuis SQLite")
        
    finally:
        # Restaurer la configuration PostgreSQL
        settings.DATABASES['default'] = original_db
        connections.close_all()
    
    return True

def clean_exported_data():
    """Nettoie les données exportées"""
    print("🧹 Nettoyage des données exportées...")
    
    try:
        # Essayer différents encodages
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        data = None
        
        for encoding in encodings:
            try:
                with open('temp_data.json', 'r', encoding=encoding) as f:
                    data = json.load(f)
                print(f"✅ Encodage détecté : {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except json.JSONDecodeError:
                continue
        
        if data is None:
            print("❌ Impossible de lire le fichier avec les encodages testés")
            return False
        
        if len(data) == 0:
            print("❌ Le fichier d'export est vide")
            return False
        
        print(f"📊 {len(data)} objets exportés")
        
        # Filtrer les données problématiques
        cleaned_data = []
        for item in data:
            # Exclure les contenttypes et permissions qui seront recréés
            if item['model'] not in ['contenttypes.contenttype', 'auth.permission']:
                cleaned_data.append(item)
        
        print(f"🧹 {len(cleaned_data)} objets après nettoyage")
        
        # Sauvegarder les données nettoyées
        with open('temp_data_cleaned.json', 'w', encoding='utf-8', errors='ignore') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Données nettoyées sauvegardées")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")
        return False
    
    return True

def import_to_postgresql():
    """Importe les données dans PostgreSQL"""
    print("📥 Import des données dans PostgreSQL...")
    
    try:
        # Importer les données nettoyées
        execute_from_command_line(['manage.py', 'loaddata', 'temp_data_cleaned.json'])
        
        print("✅ Données importées dans PostgreSQL")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'import : {e}")
        return False
    
    return True

def verify_migration():
    """Vérifie la migration"""
    print("🔍 Vérification de la migration...")
    
    try:
        from django.db import connections
        
        with connections['default'].cursor() as cursor:
            # Compter les enregistrements dans les principales tables
            tables = [
                ('classes_schoolclass', 'Classes'),
                ('students_student', 'Élèves'),
                ('subjects_subject', 'Matières'),
                ('teachers_teacher', 'Enseignants'),
                ('authentication_user', 'Utilisateurs')
            ]
            
            for table, name in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"📊 {name}: {count}")
                except Exception as e:
                    print(f"❌ Erreur pour {name}: {e}")
        
        print("✅ Vérification terminée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")

def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    print("🧹 Nettoyage des fichiers temporaires...")
    
    temp_files = ['temp_data.json', 'temp_data_cleaned.json']
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ {file} supprimé")
    
    print("✅ Fichiers temporaires supprimés")

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🚀 MIGRATION FINALE SQLITE → POSTGRESQL - SCOLARIS")
    print("=" * 70)
    
    # Sauvegarde
    backup_file = backup_sqlite()
    
    try:
        # Export depuis SQLite
        if not export_from_sqlite():
            return
        
        # Nettoyage des données
        if not clean_exported_data():
            return
        
        # Import dans PostgreSQL
        if not import_to_postgresql():
            return
        
        # Vérification
        verify_migration()
        
        print("\n" + "=" * 70)
        print("🎉 MIGRATION RÉUSSIE !")
        print("=" * 70)
        print(f"📁 Sauvegarde SQLite : {backup_file}")
        print("💡 Vous pouvez maintenant supprimer db.sqlite3")
        print("💡 Redémarrez votre serveur Django")
        
    except Exception as e:
        print(f"\n❌ Erreur critique : {e}")
        print("La migration a échoué. Vérifiez les logs ci-dessus.")
    
    finally:
        # Nettoyage des fichiers temporaires
        cleanup_temp_files()

if __name__ == '__main__':
    main()
