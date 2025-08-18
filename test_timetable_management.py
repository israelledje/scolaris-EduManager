#!/usr/bin/env python
"""
Script de test pour la gestion manuelle de l'emploi du temps
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from classes.models import SchoolClass
from subjects.models import Subject, SubjectProgram, TimetableSlot
from teachers.models import Teacher
from school.models import SchoolYear

def test_timetable_management():
    """Teste la gestion manuelle de l'emploi du temps"""
    
    print("🧪 Test de la gestion manuelle de l'emploi du temps")
    print("=" * 60)
    
    try:
        # Récupérer une classe de test
        school_class = SchoolClass.objects.first()
        if not school_class:
            print("❌ Aucune classe trouvée")
            return
        
        print(f"✅ Classe de test: {school_class.name}")
        
        # Récupérer des matières et enseignants
        subjects = Subject.objects.all()[:3]
        teachers = Teacher.objects.all()[:3]
        
        if not subjects.exists():
            print("❌ Aucune matière trouvée")
            return
        
        if not teachers.exists():
            print("❌ Aucun enseignant trouvé")
            return
        
        print(f"✅ {subjects.count()} matières trouvées")
        print(f"✅ {teachers.count()} enseignants trouvés")
        
        # Créer des programmes pédagogiques de test
        current_year = SchoolYear.get_active_year() or SchoolYear.objects.first()
        
        # Supprimer les programmes existants
        SubjectProgram.objects.filter(school_class=school_class).delete()
        
        # Créer des programmes avec des horaires réalistes
        programs_data = [
            {'subject': subjects[0], 'hours': 4, 'name': 'Mathématiques'},
            {'subject': subjects[1] if subjects.count() > 1 else subjects[0], 'hours': 3, 'name': 'Français'},
            {'subject': subjects[2] if subjects.count() > 2 else subjects[0], 'hours': 2, 'name': 'Histoire'},
        ]
        
        created_programs = []
        for data in programs_data:
            program = SubjectProgram.objects.create(
                subject=data['subject'],
                school_class=school_class,
                school_year=current_year,
                title=f"Programme {data['name']} - Test",
                description=f"Programme de test pour {data['name']}",
                total_hours=data['hours'],
                is_active=True,
                is_approved=True
            )
            created_programs.append(program)
            print(f"✅ Programme créé: {data['name']} ({data['hours']}h/semaine)")
        
        # Supprimer les créneaux existants
        TimetableSlot.objects.filter(class_obj=school_class).delete()
        
        # Créer quelques créneaux de test
        test_slots = [
            {'day': 1, 'period': 1, 'subject': subjects[0], 'teacher': teachers[0]},  # Lundi 8h-9h
            {'day': 1, 'period': 2, 'subject': subjects[0], 'teacher': teachers[0]},  # Lundi 9h-10h
            {'day': 2, 'period': 1, 'subject': subjects[1], 'teacher': teachers[1]},  # Mardi 8h-9h
            {'day': 3, 'period': 3, 'subject': subjects[2], 'teacher': teachers[2]},  # Mercredi 10h-11h
        ]
        
        for slot_data in test_slots:
            slot = TimetableSlot.objects.create(
                class_obj=school_class,
                subject=slot_data['subject'],
                teacher=slot_data['teacher'],
                day=slot_data['day'],
                period=slot_data['period'],
                duration=1,
                year=current_year
            )
            print(f"✅ Créneau créé: {slot_data['subject'].name} - {slot.get_day_display()} {slot.get_period_display()}")
        
        # Vérifier les statistiques
        total_hours = sum(program.total_hours for program in created_programs)
        total_slots = TimetableSlot.objects.filter(class_obj=school_class).count()
        
        print(f"\n📊 Statistiques:")
        print(f"   • Total des heures demandées: {total_hours}h/semaine")
        print(f"   • Créneaux créés: {total_slots}")
        print(f"   • Limite scolaire: 36h/semaine")
        
        if total_hours <= 36:
            print(f"   ✅ Total dans les limites scolaires")
        else:
            print(f"   ⚠️  Total dépassant la limite (sera ajusté automatiquement)")
        
        print(f"\n🚀 Test terminé avec succès!")
        print(f"   • URL de gestion: /subjects/pedagogy/class/{school_class.id}/timetable/")
        print(f"   • URL de détail de classe: /classes/classes/{school_class.id}/")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_timetable_management()
