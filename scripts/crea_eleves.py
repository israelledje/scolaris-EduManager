#!/usr/bin/env python
"""
Script Django — Génération de classes et élèves
Exécution: python scripts/crea_eleves.py
"""
import os
import sys
import django
import random
from datetime import date, timedelta

# Ajouter le répertoire parent au path Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.db import transaction
from school.models import School, SchoolYear, SchoolLevel, EducationSystem
from classes.models import SchoolClass
from students.models import Student

# ──────────────────────────────────────────────
# PARAMÈTRES : 20 élèves par classe
# ──────────────────────────────────────────────
CLASSES_CONFIG = [
    # Niveau Collège (6e à 3e)
    {"name": "6e M1", "level_name": "Collège", "system_code": "FR"},
    {"name": "5e M1", "level_name": "Collège", "system_code": "FR"},
    {"name": "4e A1", "level_name": "Collège", "system_code": "FR"},
    {"name": "4e E1", "level_name": "Collège", "system_code": "FR"},
    {"name": "3e A1", "level_name": "Collège", "system_code": "FR"},
    {"name": "3e E1", "level_name": "Collège", "system_code": "FR"},
    
    # Niveau Lycée (2nd à Terminale)
    {"name": "2nd A", "level_name": "Lycée", "system_code": "FR"},
    {"name": "2nd C", "level_name": "Lycée", "system_code": "FR"},
    {"name": "2nd TI", "level_name": "Lycée", "system_code": "FR"},
    {"name": "1ère A", "level_name": "Lycée", "system_code": "FR"},
    {"name": "1ère C", "level_name": "Lycée", "system_code": "FR"},
    {"name": "1ère TI", "level_name": "Lycée", "system_code": "FR"},
    {"name": "1ère D", "level_name": "Lycée", "system_code": "FR"},
    {"name": "Tle A", "level_name": "Lycée", "system_code": "FR"},
    {"name": "Tle D", "level_name": "Lycée", "system_code": "FR"},
    {"name": "Tle TI", "level_name": "Lycée", "system_code": "FR"},
    {"name": "Tle C", "level_name": "Lycée", "system_code": "FR"},
]

STUDENTS_PER_CLASS = 20

# Exemple de prénoms et noms camerounais
FIRST_NAMES_M = ["Jean", "Paul", "David", "Eric", "Luc", "Alain", "Simon", "Serge", "Patrick", "Roger", 
                  "Christian", "Emmanuel", "Thierry", "Olivier", "Laurent", "Michel", "André", "Pierre", "François", "Marc"]
FIRST_NAMES_F = ["Marie", "Clarisse", "Aline", "Flore", "Nathalie", "Brigitte", "Solange", "Mireille", "Sandrine", "Pauline",
                  "Christelle", "Emmanuelle", "Thérèse", "Olivia", "Laure", "Michèle", "Andrée", "Pierrette", "Françoise", "Marine"]
LAST_NAMES = ["Ndongo", "Essomba", "Mouafo", "Tchoua", "Abena", "Ngong", "Nfor", "Nana", "Ongene", "Fouda",
              "Mbarga", "Nkeng", "Tchoua", "Abena", "Ngong", "Nfor", "Nana", "Ongene", "Fouda", "Essomba"]

BIRTH_PLACES = ["Yaoundé", "Douala", "Bafoussam", "Bertoua", "Bamenda", "Garoua", "Ngaoundéré", "Ebolowa", "Kribi", "Maroua",
                "Dschang", "Kumba", "Buea", "Limbé", "Edea", "Mbalmayo", "Sangmelima", "Mamfe", "Bali", "Kumbo"]

def ensure_education_system_and_levels():
    """Crée le système éducatif francophone et les niveaux s'ils n'existent pas"""
    print("🔧 Vérification/Création du système éducatif et des niveaux...")
    
    # Créer le système éducatif francophone
    system, created = EducationSystem.objects.get_or_create(
        code="FR",
        defaults={"name": "Système Francophone"}
    )
    if created:
        print(f"  ✅ Système éducatif créé : {system.name}")
    else:
        print(f"  ♻️ Système éducatif existant : {system.name}")
    
    # Créer les niveaux scolaires
    levels_data = [
        {"name": "Collège", "order": 1},
        {"name": "Lycée", "order": 2},
    ]
    
    levels_created = {}
    for level_data in levels_data:
        level, created = SchoolLevel.objects.get_or_create(
            name=level_data["name"],
            system=system,
            defaults={"order": level_data["order"]}
        )
        levels_created[level_data["name"]] = level
        if created:
            print(f"  ✅ Niveau créé : {level.name}")
        else:
            print(f"  ♻️ Niveau existant : {level.name}")
    
    return system, levels_created

def main():
    print("🚀 Début de la génération des classes et élèves...")
    
    # ──────────────────────────────────────────────
    # Vérification/Création du système éducatif et niveaux
    # ──────────────────────────────────────────────
    system, levels = ensure_education_system_and_levels()
    
    # ──────────────────────────────────────────────
    # Récupération d'une School et SchoolYear
    # ──────────────────────────────────────────────
    school = School.objects.first()
    year = SchoolYear.objects.first()

    if not school or not year:
        print("❌ Aucune School ou SchoolYear trouvée. Impossible de continuer.")
        print("💡 Assurez-vous d'avoir configuré l'établissement et l'année scolaire.")
        return

    print(f"🏫 Établissement : {school.name}")
    print(f"📅 Année scolaire : {year.annee}")
    print(f"📚 Nombre de classes à traiter : {len(CLASSES_CONFIG)}")
    print(f"👨‍🎓 Élèves par classe : {STUDENTS_PER_CLASS}")
    print()

    # ──────────────────────────────────────────────
    # Génération de classes + élèves
    # ──────────────────────────────────────────────
    total_students_created = 0
    total_students_existing = 0
    
    with transaction.atomic():
        for class_config in CLASSES_CONFIG:
            class_name = class_config["name"]
            level_name = class_config["level_name"]
            level = levels[level_name]
            
            print(f"🔍 Traitement de la classe : {class_name} (Niveau: {level_name})")
            
            # Création de la classe si inexistante
            school_class, created = SchoolClass.objects.get_or_create(
                name=class_name,
                level=level,
                year=year,
                school=school,
                defaults={
                    "capacity": STUDENTS_PER_CLASS,
                    "is_active": True
                }
            )
            if created:
                print(f"  ✅ Classe créée : {class_name}")
            else:
                print(f"  ♻️ Classe existante : {class_name}")

            # Comptage des élèves existants
            existing_students = Student.objects.filter(current_class=school_class, year=year).count()
            total_students_existing += existing_students
            
            if existing_students >= STUDENTS_PER_CLASS:
                print(f"  ⏭️ {class_name} a déjà {existing_students} élèves, skip.")
                continue

            # Nombre d'élèves à ajouter
            to_add = STUDENTS_PER_CLASS - existing_students
            print(f"  👨‍🎓 Ajout de {to_add} élève(s) à {class_name}")

            for i in range(to_add):
                gender = random.choice(["M", "F"])
                if gender == "M":
                    first_name = random.choice(FIRST_NAMES_M)
                else:
                    first_name = random.choice(FIRST_NAMES_F)

                last_name = random.choice(LAST_NAMES)
                # Âge entre 11 et 22 ans (6e à Terminale)
                birth_date = date.today() - timedelta(days=random.randint(11*365, 22*365))
                birth_place = random.choice(BIRTH_PLACES)
                matricule = f"{class_name.replace(' ', '').replace('è', 'e').replace('nd', '2').replace('re', '1')}-{i+1:03d}"

                student = Student.objects.create(
                    matricule=matricule,
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    birth_date=birth_date,
                    birth_place=birth_place,
                    school=school,
                    year=year,
                    current_class=school_class
                )
                total_students_created += 1
                print(f"    👨‍🎓 Élève ajouté : {student.last_name} {student.first_name} ({class_name}) - {matricule}")

            print(f"  ✅ Classe {class_name} terminée avec {Student.objects.filter(current_class=school_class, year=year).count()} élèves")
            print()

    # ──────────────────────────────────────────────
    # Résumé final
    # ──────────────────────────────────────────────
    print("🎉 Génération terminée !")
    print(f"📊 Résumé :")
    print(f"   🏫 Classes traitées : {len(CLASSES_CONFIG)}")
    print(f"   👨‍🎓 Élèves existants : {total_students_existing}")
    print(f"   👨‍🎓 Nouveaux élèves créés : {total_students_created}")
    print(f"   👨‍🎓 Total élèves : {total_students_existing + total_students_created}")
    print(f"   🎯 Objectif par classe : {STUDENTS_PER_CLASS} élèves")

if __name__ == "__main__":
    main()
