#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour créer un parent de test
"""

import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire parent au path Python
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from students.models import Student, Guardian

def create_test_guardian():
    """Crée un parent de test pour un étudiant"""
    print("👨‍👩‍👧‍👦 Création d'un parent de test...")
    
    try:
        # Récupérer le premier étudiant actif
        student = Student.objects.filter(is_active=True).first()
        if not student:
            print("❌ Aucun étudiant actif trouvé")
            return
        
        print(f"👤 Étudiant sélectionné: {student}")
        
        # Vérifier s'il a déjà des parents
        existing_guardians = student.guardians.all()
        if existing_guardians.exists():
            print(f"✅ L'étudiant a déjà {existing_guardians.count()} parent(s)/tuteur(s):")
            for guardian in existing_guardians:
                print(f"  - {guardian.relation}: {guardian.name} ({guardian.phone}, {guardian.email})")
            return
        
        # Créer un parent de test
        guardian = Guardian.objects.create(
            student=student,
            name="Papa Test",
            relation="Père",
            phone="+237698072400",
            email="papa.test@example.com",
            profession="Ingénieur",
            is_emergency_contact=True
        )
        
        print(f"✅ Parent créé avec succès:")
        print(f"  - Nom: {guardian.name}")
        print(f"  - Relation: {guardian.relation}")
        print(f"  - Téléphone: {guardian.phone}")
        print(f"  - Email: {guardian.email}")
        print(f"  - Profession: {guardian.profession}")
        print(f"  - Contact d'urgence: {guardian.is_emergency_contact}")
        
        # Vérifier que le parent est bien associé à l'étudiant
        student.refresh_from_db()
        guardians = student.guardians.all()
        print(f"\n🔗 Vérification de l'association:")
        print(f"  - Étudiant: {student}")
        print(f"  - Parents associés: {guardians.count()}")
        for g in guardians:
            print(f"    * {g.relation}: {g.name}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du parent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Création d'un parent de test...")
    print("=" * 50)
    create_test_guardian()
    print("=" * 50)
    print("🏁 Script terminé")
