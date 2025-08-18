#!/usr/bin/env python
"""
Script de test pour vérifier la cohérence des modèles
Exécution: python manage.py shell < scripts/test_models.py
"""

import os
import sys
import django

# Ajouter le répertoire parent au path Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.db import models
from school.models import School, SchoolYear, SchoolLevel, EducationSystem
from classes.models import SchoolClass
from students.models import Student
from subjects.models import Subject
from teachers.models import Teacher, TeachingAssignment

def test_models_consistency():
    """Teste la cohérence des modèles et leurs relations"""
    print("🔍 Test de cohérence des modèles...")
    
    # Test 1: Vérification des modèles de base
    print("\n1. Vérification des modèles de base...")
    try:
        school = School.objects.first()
        year = SchoolYear.objects.first()
        system = EducationSystem.objects.first()
        
        if school:
            print(f"   ✅ School trouvée: {school.name}")
        else:
            print("   ⚠️ Aucune School trouvée")
            
        if year:
            print(f"   ✅ SchoolYear trouvée: {year.annee}")
        else:
            print("   ⚠️ Aucune SchoolYear trouvée")
            
        if system:
            print(f"   ✅ EducationSystem trouvé: {system.name}")
        else:
            print("   ⚠️ Aucun EducationSystem trouvé")
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des modèles de base: {e}")
    
    # Test 2: Vérification des niveaux scolaires
    print("\n2. Vérification des niveaux scolaires...")
    try:
        levels = SchoolLevel.objects.all()
        if levels.exists():
            print(f"   ✅ {levels.count()} niveau(x) scolaire(s) trouvé(s):")
            for level in levels:
                print(f"      - {level.name} (Système: {level.system.name})")
        else:
            print("   ⚠️ Aucun niveau scolaire trouvé")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des niveaux: {e}")
    
    # Test 3: Vérification des classes
    print("\n3. Vérification des classes...")
    try:
        classes = SchoolClass.objects.all()
        if classes.exists():
            print(f"   ✅ {classes.count()} classe(s) trouvée(s):")
            for cls in classes:
                level_info = f" (Niveau: {cls.level.name})" if cls.level else " (Niveau: Non défini)"
                print(f"      - {cls.name}{level_info}")
        else:
            print("   ⚠️ Aucune classe trouvée")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des classes: {e}")
    
    # Test 4: Vérification des matières
    print("\n4. Vérification des matières...")
    try:
        subjects = Subject.objects.all()
        if subjects.exists():
            print(f"   ✅ {subjects.count()} matière(s) trouvée(s):")
            for subject in subjects:
                print(f"      - {subject.name} [{subject.code}] (Groupe {subject.group})")
        else:
            print("   ⚠️ Aucune matière trouvée")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des matières: {e}")
    
    # Test 5: Vérification des enseignants
    print("\n5. Vérification des enseignants...")
    try:
        teachers = Teacher.objects.all()
        if teachers.exists():
            print(f"   ✅ {teachers.count()} enseignant(s) trouvé(s):")
            for teacher in teachers:
                main_subj = f" → {teacher.main_subject.code}" if teacher.main_subject else ""
                print(f"      - {teacher.last_name} {teacher.first_name} ({teacher.matricule}){main_subj}")
        else:
            print("   ⚠️ Aucun enseignant trouvé")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des enseignants: {e}")
    
    # Test 6: Vérification des affectations d'enseignement
    print("\n6. Vérification des affectations d'enseignement...")
    try:
        assignments = TeachingAssignment.objects.all()
        if assignments.exists():
            print(f"   ✅ {assignments.count()} affectation(s) trouvée(s):")
            for assignment in assignments:
                teacher_info = f" - {assignment.teacher}" if assignment.teacher else " - Non assigné"
                print(f"      - {assignment.subject.code} → {assignment.school_class.name}{teacher_info} (coef: {assignment.coefficient}, h: {assignment.hours_per_week})")
        else:
            print("   ⚠️ Aucune affectation d'enseignement trouvée")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des affectations: {e}")
    
    # Test 7: Vérification des élèves
    print("\n7. Vérification des élèves...")
    try:
        students = Student.objects.all()
        if students.exists():
            print(f"   ✅ {students.count()} élève(s) trouvé(s):")
            for student in students:
                class_info = f" → {student.current_class.name}" if student.current_class else " (Classe: Non assignée)"
                print(f"      - {student.last_name} {student.first_name} ({student.matricule}){class_info}")
        else:
            print("   ⚠️ Aucun élève trouvé")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des élèves: {e}")
    
    print("\n🎯 Test de cohérence terminé !")

def test_model_fields():
    """Teste les champs des modèles pour vérifier leur cohérence"""
    print("\n🔍 Test des champs des modèles...")
    
    # Test des champs du modèle Student
    print("\n1. Modèle Student:")
    try:
        student_fields = Student._meta.get_fields()
        required_fields = ['matricule', 'first_name', 'last_name', 'gender', 'birth_date', 'birth_place']
        for field_name in required_fields:
            field = Student._meta.get_field(field_name)
            if field.null and field.blank:
                print(f"   ✅ {field_name}: nullable et blank")
            elif field.null:
                print(f"   ✅ {field_name}: nullable")
            elif field.blank:
                print(f"   ✅ {field_name}: blank")
            else:
                print(f"   ✅ {field_name}: requis")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des champs Student: {e}")
    
    # Test des champs du modèle SchoolClass
    print("\n2. Modèle SchoolClass:")
    try:
        class_fields = SchoolClass._meta.get_fields()
        required_fields = ['name', 'level', 'year', 'school']
        for field_name in required_fields:
            field = SchoolClass._meta.get_field(field_name)
            if field.null and field.blank:
                print(f"   ✅ {field_name}: nullable et blank")
            elif field.null:
                print(f"   ✅ {field_name}: nullable")
            elif field.blank:
                print(f"   ✅ {field_name}: blank")
            else:
                print(f"   ✅ {field_name}: requis")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des champs SchoolClass: {e}")
    
    print("\n🎯 Test des champs terminé !")

if __name__ == "__main__":
    print("🚀 Début des tests de cohérence...")
    test_models_consistency()
    test_model_fields()
    print("\n🎉 Tous les tests sont terminés !")
