#!/usr/bin/env python3
"""
Script de vérification du curriculum scolaire
===========================================

Ce script affiche toutes les matières par classe pour vérifier 
la conformité avec le programme officiel camerounais.

Usage:
    cd scolaris
    python scripts/verify_curriculum.py
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from classes.models import SchoolClass
from teachers.models import TeachingAssignment
from subjects.models import Subject
from school.models import SchoolYear

def verify_curriculum():
    """Vérifie et affiche le curriculum par classe"""
    print("🔍 VÉRIFICATION DU CURRICULUM SCOLAIRE")
    print("=" * 60)
    
    # Récupérer l'année active
    active_year = SchoolYear.get_active_year()
    if not active_year:
        print("❌ Aucune année scolaire active trouvée.")
        return
    
    print(f"📅 Année scolaire: {active_year.annee}")
    print("-" * 60)
    
    # Récupérer toutes les classes
    classes = SchoolClass.objects.filter(year=active_year, is_active=True).order_by('name')
    
    if not classes.exists():
        print("❌ Aucune classe trouvée pour l'année active.")
        return
    
    total_subjects = 0
    total_assignments = 0
    
    for school_class in classes:
        print(f"\n📚 CLASSE: {school_class.name}")
        print(f"   📊 Capacité: {school_class.capacity} élèves")
        print(f"   👨‍🏫 Professeur titulaire: {school_class.main_teacher or 'Non assigné'}")
        print(f"   👥 Élèves inscrits: {school_class.student_count}")
        
        # Récupérer les affectations pour cette classe
        assignments = TeachingAssignment.objects.filter(
            school_class=school_class,
            year=active_year
        ).select_related('subject', 'teacher').order_by('subject__name')
        
        if assignments.exists():
            print(f"   📖 Matières enseignées ({assignments.count()}):")
            
            for assignment in assignments:
                subject = assignment.subject
                teacher = assignment.teacher
                coeff = assignment.coefficient
                hours = assignment.hours_per_week
                
                print(f"      • {subject.name} ({subject.code})")
                print(f"        └─ Enseignant: {teacher}")
                print(f"        └─ Coefficient: {coeff} | Heures/semaine: {hours}")
                
                total_assignments += 1
        else:
            print("   ⚠️  Aucune matière assignée à cette classe!")
        
        print("-" * 40)
    
    # Statistiques globales
    total_subjects_in_db = Subject.objects.count()
    total_teachers = set()
    for assignment in TeachingAssignment.objects.filter(year=active_year):
        if assignment.teacher:
            total_teachers.add(assignment.teacher.id)
    
    print(f"\n📊 STATISTIQUES GLOBALES:")
    print(f"   • Classes actives: {classes.count()}")
    print(f"   • Matières disponibles: {total_subjects_in_db}")
    print(f"   • Affectations créées: {total_assignments}")
    print(f"   • Enseignants impliqués: {len(total_teachers)}")
    
    # Vérification de la couverture
    print(f"\n🎯 VÉRIFICATION DE LA COUVERTURE:")
    
    # Matières sans affectation
    assigned_subjects = set()
    for assignment in TeachingAssignment.objects.filter(year=active_year):
        assigned_subjects.add(assignment.subject.id)
    
    unassigned_subjects = Subject.objects.exclude(id__in=assigned_subjects)
    if unassigned_subjects.exists():
        print(f"   ⚠️  Matières non assignées ({unassigned_subjects.count()}):")
        for subject in unassigned_subjects:
            print(f"      • {subject.name} ({subject.code})")
    else:
        print("   ✅ Toutes les matières sont assignées!")
    
    # Classes sans professeur titulaire
    classes_without_main_teacher = classes.filter(main_teacher__isnull=True)
    if classes_without_main_teacher.exists():
        print(f"   ⚠️  Classes sans professeur titulaire ({classes_without_main_teacher.count()}):")
        for class_obj in classes_without_main_teacher:
            print(f"      • {class_obj.name}")
    else:
        print("   ✅ Toutes les classes ont un professeur titulaire!")
    
    print("\n" + "=" * 60)
    print("✅ VÉRIFICATION TERMINÉE")
    print("=" * 60)

def show_subjects_by_category():
    """Affiche toutes les matières par catégorie"""
    print("\n🎓 MATIÈRES PAR CATÉGORIE")
    print("=" * 60)
    
    subjects = Subject.objects.all().order_by('group', 'name')
    
    group_1_subjects = subjects.filter(group=1)
    group_2_subjects = subjects.filter(group=2)
    
    print(f"\n📚 GROUPE 1 - Matières Littéraires ({group_1_subjects.count()}):")
    for subject in group_1_subjects:
        print(f"   • {subject.name} ({subject.code})")
    
    print(f"\n🔬 GROUPE 2 - Matières Scientifiques ({group_2_subjects.count()}):")
    for subject in group_2_subjects:
        print(f"   • {subject.name} ({subject.code})")
    
    print(f"\n📊 TOTAL: {subjects.count()} matières")

if __name__ == "__main__":
    try:
        verify_curriculum()
        show_subjects_by_category()
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        sys.exit(1)
