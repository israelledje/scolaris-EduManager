#!/usr/bin/env python
"""
Script pour lier UNIQUEMENT les utilisateurs EXISTANTS aux profils d'enseignants.
Ce script ne crée PAS de nouveaux utilisateurs automatiquement.
La création de comptes utilisateurs pour les enseignants doit être faite manuellement
selon les besoins réels d'accès au système.
"""

import os
import sys
import django

# Ajouter le chemin vers le projet Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.db import transaction
from authentication.models import User
from teachers.models import Teacher

def link_existing_users_to_teachers():
    """
    Lie UNIQUEMENT les utilisateurs de type PROFESSEUR existants 
    aux profils Teacher correspondants.
    Ne crée pas de nouveaux utilisateurs automatiquement.
    """
    
    print("🔗 Liaison des utilisateurs EXISTANTS aux profils enseignants...")
    
    # Récupérer tous les utilisateurs professeurs sans profil lié
    professor_users = User.objects.filter(role='PROFESSEUR', teacher_profile__isnull=True)
    teachers_without_user = Teacher.objects.filter(user__isnull=True)
    
    print(f"📊 Utilisateurs PROFESSEUR sans profil lié: {professor_users.count()}")
    print(f"📊 Enseignants sans utilisateur lié: {teachers_without_user.count()}")
    
    linked_count = 0
    
    with transaction.atomic():
        # Première passe : lier par email exact
        for teacher in teachers_without_user:
            if teacher.email:
                try:
                    user = User.objects.get(
                        email=teacher.email, 
                        role='PROFESSEUR',
                        teacher_profile__isnull=True
                    )
                    teacher.user = user
                    teacher.save()
                    linked_count += 1
                    print(f"✅ Lié par email: {teacher.first_name} {teacher.last_name} → {user.username}")
                except User.DoesNotExist:
                    pass
                except User.MultipleObjectsReturned:
                    print(f"⚠️  Plusieurs utilisateurs trouvés pour l'email {teacher.email}")
        
        # Deuxième passe : lier par nom exact (prénom + nom)
        teachers_still_without_user = Teacher.objects.filter(user__isnull=True)
        
        for teacher in teachers_still_without_user:
            try:
                user = User.objects.get(
                    first_name__iexact=teacher.first_name,
                    last_name__iexact=teacher.last_name,
                    role='PROFESSEUR',
                    teacher_profile__isnull=True
                )
                teacher.user = user
                teacher.save()
                linked_count += 1
                print(f"✅ Lié par nom: {teacher.first_name} {teacher.last_name} → {user.username}")
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                print(f"⚠️  Plusieurs utilisateurs trouvés pour {teacher.first_name} {teacher.last_name}")
    
    # Afficher les utilisateurs et enseignants non liés
    remaining_users = User.objects.filter(role='PROFESSEUR', teacher_profile__isnull=True)
    remaining_teachers = Teacher.objects.filter(user__isnull=True)
    
    print("\n" + "="*60)
    print("📈 RÉSUMÉ DE LA LIAISON")
    print("="*60)
    print(f"✅ Enseignants liés automatiquement: {linked_count}")
    print(f"👤 Utilisateurs PROFESSEUR non liés: {remaining_users.count()}")
    print(f"👨‍🏫 Enseignants sans compte utilisateur: {remaining_teachers.count()}")
    
    if remaining_users.exists():
        print("\n🔍 UTILISATEURS PROFESSEUR NON LIÉS:")
        for user in remaining_users:
            print(f"   - {user.get_full_name()} ({user.username}) - {user.email}")
    
    if remaining_teachers.exists():
        print("\n🔍 ENSEIGNANTS SANS COMPTE UTILISATEUR:")
        for teacher in remaining_teachers[:10]:  # Limiter l'affichage
            print(f"   - {teacher.first_name} {teacher.last_name} - {teacher.email}")
        if remaining_teachers.count() > 10:
            print(f"   ... et {remaining_teachers.count() - 10} autres")
    
    print("\n💡 RECOMMANDATIONS:")
    print("   1. Créez manuellement des comptes User pour les enseignants qui ont besoin d'accéder au système")
    print("   2. Utilisez l'interface d'administration Django pour lier manuellement les cas ambigus")
    print("   3. Tous les enseignants n'ont pas besoin d'un compte utilisateur")
    
    print("\n🎉 Liaison terminée!")

if __name__ == "__main__":
    link_existing_users_to_teachers()
