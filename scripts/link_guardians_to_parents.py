#!/usr/bin/env python
"""
Script pour lier les Guardian existants aux ParentUser correspondants
"""

import os
import sys
import django

# Ajouter le répertoire parent au chemin Python
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from students.models import Guardian, Student
from parents_portal.models import ParentUser
from django.db import transaction

def link_guardians_to_parents():
    """Lie les Guardian existants aux ParentUser correspondants"""
    
    print("🔗 Liaison des Guardian aux ParentUser...")
    
    # Récupérer tous les Guardian qui n'ont pas encore de parent_user
    guardians_without_parent = Guardian.objects.filter(parent_user__isnull=True)
    print(f"📊 {guardians_without_parent.count()} Guardian sans ParentUser trouvés")
    
    linked_count = 0
    created_count = 0
    
    with transaction.atomic():
        for guardian in guardians_without_parent:
            # Chercher un ParentUser avec le même email
            if guardian.email:
                try:
                    parent_user = ParentUser.objects.get(email=guardian.email)
                    guardian.parent_user = parent_user
                    guardian.save()
                    linked_count += 1
                    print(f"✅ Lié: {guardian.name} ({guardian.email}) → {parent_user.get_full_name()}")
                except ParentUser.DoesNotExist:
                    # Créer un nouveau ParentUser
                    try:
                        # Générer un username unique
                        base_username = f"{guardian.name.lower().replace(' ', '')}"
                        username = base_username
                        counter = 1
                        while ParentUser.objects.filter(username=username).exists():
                            username = f"{base_username}{counter}"
                            counter += 1
                        
                        # Créer le ParentUser
                        parent_user = ParentUser.objects.create(
                            username=username,
                            email=guardian.email,
                            first_name=guardian.name.split()[0] if guardian.name else "Tuteur",
                            last_name=" ".join(guardian.name.split()[1:]) if guardian.name and len(guardian.name.split()) > 1 else "Tuteur",
                            phone=guardian.phone or "",
                            role='GUARDIAN',
                            status='ACTIVE'
                        )
                        
                        # Générer un mot de passe temporaire
                        temp_password = parent_user.generate_temporary_password()
                        parent_user.set_password(temp_password)
                        parent_user.save()
                        
                        # Lier le Guardian
                        guardian.parent_user = parent_user
                        guardian.save()
                        
                        created_count += 1
                        print(f"🆕 Créé: {guardian.name} ({guardian.email}) → {parent_user.get_full_name()} (pwd: {temp_password})")
                        
                    except Exception as e:
                        print(f"❌ Erreur création ParentUser pour {guardian.name}: {e}")
                        continue
            else:
                print(f"⚠️  Guardian {guardian.name} sans email - impossible de lier")
    
    print(f"\n📈 Résumé:")
    print(f"   - Guardian liés: {linked_count}")
    print(f"   - ParentUser créés: {created_count}")
    print(f"   - Total traité: {linked_count + created_count}")

def show_current_status():
    """Affiche le statut actuel des liaisons"""
    
    print("\n📊 Statut actuel des liaisons:")
    
    total_guardians = Guardian.objects.count()
    linked_guardians = Guardian.objects.filter(parent_user__isnull=False).count()
    unlinked_guardians = Guardian.objects.filter(parent_user__isnull=True).count()
    
    print(f"   - Total Guardian: {total_guardians}")
    print(f"   - Guardian liés: {linked_guardians}")
    print(f"   - Guardian non liés: {unlinked_guardians}")
    
    if linked_guardians > 0:
        print(f"\n🔗 Guardian liés:")
        for guardian in Guardian.objects.filter(parent_user__isnull=False).select_related('parent_user', 'student'):
            print(f"   - {guardian.name} → {guardian.parent_user.get_full_name()} (Étudiant: {guardian.student})")
    
    if unlinked_guardians > 0:
        print(f"\n⚠️  Guardian non liés:")
        for guardian in Guardian.objects.filter(parent_user__isnull=True).select_related('student'):
            print(f"   - {guardian.name} (Étudiant: {guardian.student}) - Email: {guardian.email or 'Aucun'}")

if __name__ == "__main__":
    print("🚀 Script de liaison Guardian-ParentUser")
    print("=" * 50)
    
    show_current_status()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--link":
        print("\n" + "=" * 50)
        link_guardians_to_parents()
        print("\n" + "=" * 50)
        show_current_status()
    else:
        print("\n💡 Pour lier les Guardian, exécutez: python link_guardians_to_parents.py --link")
