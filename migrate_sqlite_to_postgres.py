#!/usr/bin/env python
"""
Script de migration robuste de SQLite vers PostgreSQL pour Scolaris
Gère les contraintes, séquences et relations entre tables
"""

import os
import sys
import django
import json
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.db import connections
from django.core.management import execute_from_command_line
from django.core.management.base import CommandError

def backup_sqlite_data():
    """Sauvegarde des données SQLite avant migration"""
    print("🔄 Sauvegarde des données SQLite...")
    
    import shutil
    
    backup_dir = 'backup_sqlite'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{backup_dir}/db_backup_{timestamp}.sqlite3"
    
    # Copier la base SQLite
    shutil.copy2('db.sqlite3', backup_file)
    print(f"✅ Sauvegarde créée : {backup_file}")
    
    return backup_file

def reset_postgresql_database():
    """Réinitialise la base PostgreSQL"""
    print("🗑️ Réinitialisation de la base PostgreSQL...")
    
    try:
        # Supprimer toutes les tables
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """)
        
        print("✅ Base PostgreSQL réinitialisée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation : {e}")
        return False
    
    return True

def create_postgresql_schema():
    """Crée le schéma PostgreSQL"""
    print("📋 Création du schéma PostgreSQL...")
    
    try:
        # Créer les migrations
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # Appliquer les migrations
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Schéma PostgreSQL créé")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du schéma : {e}")
        return False
    
    return True

def export_sqlite_data():
    """Exporte les données SQLite en JSON"""
    print("💾 Export des données SQLite...")
    
    try:
        # Exporter toutes les données
        execute_from_command_line(['manage.py', 'dumpdata', '--indent', '2', '-o', 'temp_data.json'])
        
        print("✅ Données exportées vers temp_data.json")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export : {e}")
        return False
    
    return True

def clean_exported_data():
    """Nettoie les données exportées pour PostgreSQL"""
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
        
        # Filtrer les données problématiques
        cleaned_data = []
        for item in data:
            # Exclure les contenttypes et permissions qui seront recréés
            if item['model'] not in ['contenttypes.contenttype', 'auth.permission']:
                cleaned_data.append(item)
        
        # Sauvegarder les données nettoyées avec l'encodage approprié
        with open('temp_data_cleaned.json', 'w', encoding='utf-8', errors='ignore') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Données nettoyées sauvegardées dans temp_data_cleaned.json")
        
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

def fix_postgresql_sequences():
    """Corrige les séquences PostgreSQL"""
    print("🔧 Correction des séquences PostgreSQL...")
    
    try:
        with connections['default'].cursor() as cursor:
            # Récupérer toutes les tables avec des séquences
            cursor.execute("""
                SELECT table_name, column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND column_default LIKE 'nextval%'
            """)
            
            sequences = cursor.fetchall()
            
            for table_name, column_name in sequences:
                # Réinitialiser la séquence
                cursor.execute(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', '{column_name}'),
                        COALESCE(MAX({column_name}), 1)
                    ) FROM {table_name}
                """)
        
        print("✅ Séquences PostgreSQL corrigées")
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction des séquences : {e}")
        return False
    
    return True

def verify_migration():
    """Vérifie la migration"""
    print("🔍 Vérification de la migration...")
    
    try:
        # Compter les enregistrements dans les principales tables
        from django.contrib.auth.models import User
        from classes.models import SchoolClass, Student
        from subjects.models import Subject
        from teachers.models import Teacher
        
        print(f"👥 Utilisateurs : {User.objects.count()}")
        print(f"🏫 Classes : {SchoolClass.objects.count()}")
        print(f"👨‍🎓 Élèves : {Student.objects.count()}")
        print(f"📚 Matières : {Subject.objects.count()}")
        print(f"👨‍🏫 Enseignants : {Teacher.objects.count()}")
        
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
    print("🚀 MIGRATION ROBUSTE SQLITE → POSTGRESQL - SCOLARIS")
    print("=" * 70)
    
    # Vérifier que PostgreSQL est accessible
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"🔗 Connexion PostgreSQL OK : {version[0]}")
    except Exception as e:
        print(f"❌ Impossible de se connecter à PostgreSQL : {e}")
        print("Vérifiez votre configuration dans settings.py")
        return
    
    # Vérifier si PostgreSQL a déjà des tables
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            table_count = cursor.fetchone()[0]
            
        if table_count > 0:
            print(f"📋 PostgreSQL contient déjà {table_count} tables")
            print("🔄 Reprise de la migration depuis l'export des données...")
            
            # Sauvegarde
            backup_file = backup_sqlite_data()
            
            try:
                # Export des données (si pas déjà fait)
                if not os.path.exists('temp_data.json'):
                    if not export_sqlite_data():
                        return
                
                # Nettoyage des données
                if not clean_exported_data():
                    return
                
                # Import dans PostgreSQL
                if not import_to_postgresql():
                    return
                
                # Correction des séquences
                if not fix_postgresql_sequences():
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
            
            return
    
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification des tables : {e}")
        print("🔄 Continuons avec la migration complète...")
    
    # Migration complète
    # Sauvegarde
    backup_file = backup_sqlite_data()
    
    try:
        # Réinitialisation de PostgreSQL
        if not reset_postgresql_database():
            return
        
        # Création du schéma
        if not create_postgresql_schema():
            return
        
        # Export des données
        if not export_sqlite_data():
            return
        
        # Nettoyage des données
        if not clean_exported_data():
            return
        
        # Import dans PostgreSQL
        if not import_to_postgresql():
            return
        
        # Correction des séquences
        if not fix_postgresql_sequences():
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
