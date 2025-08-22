#!/usr/bin/env python
"""
Script pour corriger la configuration de la base de données
et s'assurer que toutes les tables nécessaires sont créées.
"""

import os
import sys
import django

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.conf import settings
import sqlite3

def check_database_tables():
    """
    Vérifie si les tables essentielles existent
    """
    print("🔍 Vérification des tables de la base de données...")
    
    with connection.cursor() as cursor:
        # Vérifier les tables Django essentielles
        essential_tables = [
            'django_migrations',
            'django_session',
            'django_content_type',
            'auth_permission',
            'authentication_user',
            'authentication_user_groups',
            'authentication_user_user_permissions',
        ]
        
        # Obtenir la liste des tables existantes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = []
        for table in essential_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"❌ Tables manquantes: {', '.join(missing_tables)}")
            return False
        else:
            print("✅ Toutes les tables essentielles sont présentes")
            return True

def apply_migrations():
    """
    Applique toutes les migrations nécessaires
    """
    print("\n📊 Application des migrations...")
    
    try:
        # Créer les migrations si nécessaire
        print("Création des migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # Appliquer les migrations
        print("Application des migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Migrations appliquées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'application des migrations: {e}")
        return False

def create_superuser_if_needed():
    """
    Créer un superutilisateur si aucun n'existe
    """
    from authentication.models import User
    
    print("\n👤 Vérification des utilisateurs administrateurs...")
    
    admin_users = User.objects.filter(role='ADMIN', is_superuser=True)
    
    if not admin_users.exists():
        print("Aucun administrateur trouvé. Création d'un superutilisateur...")
        
        # Créer un utilisateur admin par défaut
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@scolaris.local',
            password='admin123',
            first_name='Administrateur',
            last_name='Système',
            role='ADMIN',
            is_staff=True,
            is_superuser=True
        )
        
        print("✅ Superutilisateur créé:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Email: admin@scolaris.local")
        print("   ⚠️  CHANGEZ CE MOT DE PASSE EN PRODUCTION!")
        
    else:
        print(f"✅ {admin_users.count()} administrateur(s) trouvé(s)")

def main():
    """
    Fonction principale
    """
    print("🚀 Script de configuration de la base de données")
    print("=" * 50)
    
    # Vérifier si la base de données existe
    db_path = settings.DATABASES['default']['NAME']
    if not os.path.exists(db_path):
        print(f"📁 Création de la base de données: {db_path}")
    
    # Appliquer les migrations
    if apply_migrations():
        # Vérifier les tables
        if check_database_tables():
            # Créer un superutilisateur si nécessaire
            create_superuser_if_needed()
            
            print("\n🎉 Configuration terminée avec succès!")
            print("\nVous pouvez maintenant:")
            print("1. Démarrer le serveur: python manage.py runserver")
            print("2. Vous connecter avec admin/admin123")
            print("3. Créer des données de test")
            
        else:
            print("\n❌ Problème avec les tables de la base de données")
            return False
    else:
        print("\n❌ Échec de l'application des migrations")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
