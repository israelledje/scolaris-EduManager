#!/usr/bin/env python
"""
Script pour recréer toutes les données dans PostgreSQL
Utilise les scripts existants du dossier scripts/
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.db import connections
from django.core.management import execute_from_command_line

def reset_postgresql():
    """Vide complètement PostgreSQL"""
    print("🗑️ Vidage de PostgreSQL...")
    
    try:
        with connections['default'].cursor() as cursor:
            # Supprimer toutes les tables
            cursor.execute("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """)
        
        print("✅ PostgreSQL vidé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du vidage : {e}")
        return False

def recreate_schema():
    """Recrée le schéma PostgreSQL"""
    print("📋 Recréation du schéma PostgreSQL...")
    
    try:
        # Créer les migrations
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # Appliquer les migrations
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Schéma PostgreSQL recréé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du schéma : {e}")
        return False

def create_initial_data():
    """Crée les données initiales (école, année scolaire, etc.)"""
    print("🏫 Création des données initiales...")
    
    try:
        # Créer une école
        from school.models import School, SchoolYear
        
        school, created = School.objects.get_or_create(
            name="Lycée Bilingue de Yaoundé",
            defaults={
                'address': 'Yaoundé, Cameroun',
                'phone': '+237 222 123 456',
                'email': 'contact@lby.cm'
            }
        )
        if created:
            print("✅ École créée")
        else:
            print("♻️ École existante")
        
        # Créer une année scolaire
        year, created = SchoolYear.objects.get_or_create(
            annee="2024-2025",
            defaults={
                'start_date': '2024-09-01',
                'end_date': '2025-06-30',
                'is_active': True
            }
        )
        if created:
            print("✅ Année scolaire créée")
        else:
            print("♻️ Année scolaire existante")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données initiales : {e}")
        return False

def run_creation_scripts():
    """Exécute les scripts de création"""
    print("📚 Exécution des scripts de création...")
    
    try:
        # Script de création des matières
        print("📖 Création des matières...")
        exec(open('scripts/creation_matière.py').read())
        
        # Script de création des élèves
        print("👨‍🎓 Création des élèves...")
        exec(open('scripts/crea_eleves.py').read())
        
        print("✅ Scripts de création exécutés")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des scripts : {e}")
        return False

def verify_data():
    """Vérifie que les données ont été créées"""
    print("🔍 Vérification des données...")
    
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

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🚀 RECRÉATION COMPLÈTE DES DONNÉES - POSTGRESQL")
    print("=" * 70)
    
    try:
        # 1. Vider PostgreSQL
        if not reset_postgresql():
            return
        
        # 2. Recréer le schéma
        if not recreate_schema():
            return
        
        # 3. Créer les données initiales
        if not create_initial_data():
            return
        
        # 4. Exécuter les scripts de création
        if not run_creation_scripts():
            return
        
        # 5. Vérification
        verify_data()
        
        print("\n" + "=" * 70)
        print("🎉 RECRÉATION RÉUSSIE !")
        print("=" * 70)
        print("💡 Toutes les données ont été recréées dans PostgreSQL")
        print("💡 Vous pouvez maintenant supprimer db.sqlite3")
        print("💡 Redémarrez votre serveur Django")
        
    except Exception as e:
        print(f"\n❌ Erreur critique : {e}")
        print("La recréation a échoué. Vérifiez les logs ci-dessus.")

if __name__ == '__main__':
    main()
