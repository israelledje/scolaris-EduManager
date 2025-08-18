#!/usr/bin/env python
"""
Script de migration de SQLite vers PostgreSQL pour Scolaris
Ce script transfère toutes les données de la base SQLite vers PostgreSQL
"""

import os
import sys
import django
from django.conf import settings
from django.db import connections
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

def backup_sqlite_data():
    """Sauvegarde des données SQLite avant migration"""
    print("🔄 Sauvegarde des données SQLite...")
    
    # Créer une sauvegarde de la base SQLite
    import shutil
    from datetime import datetime
    
    backup_dir = 'backup_sqlite'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{backup_dir}/db_backup_{timestamp}.sqlite3"
    
    # Copier la base SQLite
    shutil.copy2('db.sqlite3', backup_file)
    print(f"✅ Sauvegarde créée : {backup_file}")
    
    return backup_file

def migrate_to_postgresql():
    """Migration des données vers PostgreSQL"""
    print("🚀 Début de la migration vers PostgreSQL...")
    
    try:
        # 1. Créer les tables dans PostgreSQL
        print("📋 Création des tables dans PostgreSQL...")
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        
        # 2. Dump des données SQLite
        print("💾 Export des données SQLite...")
        execute_from_command_line(['manage.py', 'dumpdata', '--exclude', 'contenttypes', '--exclude', 'auth.Permission', '--indent', '2', '-o', 'temp_data.json'])
        
        # 3. Import des données dans PostgreSQL
        print("📥 Import des données dans PostgreSQL...")
        execute_from_command_line(['manage.py', 'loaddata', 'temp_data.json'])
        
        # 4. Nettoyage
        if os.path.exists('temp_data.json'):
            os.remove('temp_data.json')
            print("🧹 Fichier temporaire supprimé")
        
        print("✅ Migration terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        return False
    
    return True

def verify_migration():
    """Vérification de la migration"""
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

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 MIGRATION SQLITE → POSTGRESQL - SCOLARIS")
    print("=" * 60)
    
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
    
    # Sauvegarde
    backup_file = backup_sqlite_data()
    
    # Migration
    if migrate_to_postgresql():
        verify_migration()
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION RÉUSSIE !")
        print("=" * 60)
        print(f"📁 Sauvegarde SQLite : {backup_file}")
        print("💡 Vous pouvez maintenant supprimer db.sqlite3")
        print("💡 Redémarrez votre serveur Django")
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRATION ÉCHOUÉE")
        print("=" * 60)
        print("Vérifiez les logs d'erreur ci-dessus")

if __name__ == '__main__':
    main()
