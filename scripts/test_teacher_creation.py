#!/usr/bin/env python
"""
Script de test pour vérifier la création d'enseignants
"""

import os
import sys
import django

# Ajouter le chemin vers le projet Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from teachers.forms import TeacherForm
from teachers.models import Teacher
from school.models import School, SchoolYear

def test_teacher_creation():
    """Test de création d'un enseignant"""
    
    print("🧪 Test de création d'enseignant...")
    print("=" * 50)
    
    # Vérifier les prérequis
    schools = School.objects.count()
    years = SchoolYear.objects.filter(statut='EN_COURS').count()
    
    print(f"📊 Écoles disponibles: {schools}")
    print(f"📊 Années scolaires actives: {years}")
    
    if schools == 0:
        print("❌ Aucune école disponible!")
        return
        
    if years == 0:
        print("❌ Aucune année scolaire active!")
        return
    
    # Données de test
    test_data = {
        'first_name': 'Jean',
        'last_name': 'Test',
        'birth_date': '1985-01-01',
        'birth_place': 'Douala',
        'gender': 'M',
        'nationality': 'Camerounaise',
        'address': '123 Rue Test',
        'phone': '699123456',
        'email': 'jean.test@example.com',
    }
    
    print(f"\n📝 Création d'un enseignant de test...")
    print(f"   Nom: {test_data['first_name']} {test_data['last_name']}")
    print(f"   Email: {test_data['email']}")
    
    try:
        # Créer le formulaire
        form = TeacherForm(data=test_data)
        
        print(f"\n🔍 Validation du formulaire...")
        if form.is_valid():
            print("✅ Formulaire valide")
            
            # Sauvegarder
            teacher = form.save()
            print(f"✅ Enseignant créé avec succès!")
            print(f"   ID: {teacher.id}")
            print(f"   Matricule: {teacher.matricule}")
            print(f"   École: {teacher.school}")
            print(f"   Année: {teacher.year}")
            
            # Nettoyer (supprimer l'enseignant de test)
            teacher.delete()
            print(f"🧹 Enseignant de test supprimé")
            
        else:
            print("❌ Erreurs de validation:")
            for field, errors in form.errors.items():
                print(f"   {field}: {', '.join(errors)}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création: {str(e)}")
    
    print(f"\n🎉 Test terminé!")

if __name__ == "__main__":
    test_teacher_creation()
