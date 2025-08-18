#!/usr/bin/env python
"""
Script pour finaliser l'import et vérifier la migration
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connections

def import_data():
    """Importe les données dans PostgreSQL"""
    print("📥 Import des données dans PostgreSQL...")
    
    if not os.path.exists('temp_data_direct.json'):
        print("❌ Fichier temp_data_direct.json non trouvé")
        return False
    
    try:
        # Importer les données
        execute_from_command_line(['manage.py', 'loaddata', 'temp_data_direct.json'])
        print("✅ Données importées dans PostgreSQL")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'import : {e}")
        return False

def verify_migration():
    """Vérifie la migration"""
    print("🔍 Vérification de la migration...")
    
    try:
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

def cleanup():
    """Nettoie les fichiers temporaires"""
    print("🧹 Nettoyage des fichiers temporaires...")
    
    temp_files = ['temp_data_direct.json']
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ {file} supprimé")
    
    print("✅ Fichiers temporaires supprimés")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 FINALISATION DE LA MIGRATION")
    print("=" * 60)
    
    # Import des données
    if import_data():
        # Vérification
        verify_migration()
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION TERMINÉE !")
        print("=" * 60)
        print("💡 Vous pouvez maintenant supprimer db.sqlite3")
        print("💡 Redémarrez votre serveur Django")
        
    else:
        print("\n❌ La migration a échoué")
    
    # Nettoyage
    cleanup()

if __name__ == '__main__':
    main()
