#!/usr/bin/env python
"""
Script pour créer des matières et des enseignants avec leurs affectations
Exécution: python manage.py shell < scripts/creation_matiere.py
"""

import os
import sys
import django

# Ajouter le répertoire parent au path Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.db import transaction
from datetime import date
from subjects.models import Subject
from teachers.models import Teacher, TeachingAssignment
from school.models import School, SchoolYear
from classes.models import SchoolClass

# ────────────────────────────────────────────────────────────────────────────────
# Définition des matières (Groupe 1 / Groupe 2)
# ────────────────────────────────────────────────────────────────────────────────

GROUPE_1 = 1
GROUPE_2 = 2

subjects_payload = [
    # Groupe 1 — Tronc commun & sciences
    {"name": "Littérature (Français)", "code": "LIT", "group": GROUPE_1, "description": "Analyse de textes, grammaire, rédaction."},
    {"name": "Anglais", "code": "ANG", "group": GROUPE_1, "description": "Langue anglaise."},
    {"name": "Mathématiques", "code": "MATH", "group": GROUPE_1, "description": "Algèbre, analyse, géométrie, statistiques."},
    {"name": "Physique-Chimie", "code": "PC", "group": GROUPE_1, "description": "Physique et chimie (hors PCT)."},
    {"name": "SVT", "code": "SVT", "group": GROUPE_1, "description": "Sciences de la Vie et de la Terre."},
    {"name": "PCT (Physique-Chimie-Technologie)", "code": "PCT", "group": GROUPE_1, "description": "Applicable surtout en 4e et 3e."},
    {"name": "Informatique (Générale)", "code": "INFO", "group": GROUPE_1, "description": "TIC, bureautique, notions de base."},
    {"name": "Travail Manuel (TM)", "code": "TM", "group": GROUPE_1, "description": "Ateliers pratiques, travaux manuels."},

    # Groupe 2 — Lettres & disciplines complémentaires
    {"name": "Histoire", "code": "HIST", "group": GROUPE_2, "description": "Histoire générale et du Cameroun."},
    {"name": "Géographie", "code": "GEO", "group": GROUPE_2, "description": "Géographie physique et humaine."},
    {"name": "Philosophie", "code": "PHILO", "group": GROUPE_2, "description": "Logique, morale, auteurs et doctrines."},
    {"name": "Espagnol", "code": "ESP", "group": GROUPE_2, "description": "Langue vivante."},
    {"name": "Allemand", "code": "ALL", "group": GROUPE_2, "description": "Langue vivante."},
    {"name": "Éducation Civique et Morale (ECM)", "code": "ECM", "group": GROUPE_2, "description": "Citoyenneté, institutions, valeurs."},
    {"name": "Éducation Physique et Sportive (EPS)", "code": "EPS", "group": GROUPE_2, "description": "Activités physiques et sportives."},
    {"name": "Arts Plastiques", "code": "ARTS", "group": GROUPE_2, "description": "Dessin, peinture, arts visuels."},
    {"name": "Musique", "code": "MUS", "group": GROUPE_2, "description": "Éducation musicale."},

    # Spécialités TI — Première & Terminale TI (Groupe 1)
    {"name": "Algorithmique & Programmation", "code": "ALGO", "group": GROUPE_1, "description": "Algorithmes, programmation structurée/OO."},
    {"name": "Structures de Données", "code": "SD", "group": GROUPE_1, "description": "Listes, piles, files, arbres, graphes."},
    {"name": "Bases de Données", "code": "BDD", "group": GROUPE_1, "description": "Modélisation, SQL, SGBD."},
    {"name": "Réseaux Informatiques", "code": "RESEAUX", "group": GROUPE_1, "description": "Modèle OSI, routage, services réseau."},
    {"name": "Architecture des Ordinateurs", "code": "ARCHI", "group": GROUPE_1, "description": "CPU, mémoire, bus, I/O."},
    {"name": "Systèmes d'Exploitation", "code": "SE", "group": GROUPE_1, "description": "Processus, threads, mémoire, systèmes de fichiers."},
    {"name": "Génie Logiciel", "code": "GL", "group": GROUPE_1, "description": "UML, cycles de développement, tests."},
]

# ────────────────────────────────────────────────────────────────────────────────
# Configuration des affectations d'enseignement par classe
# ────────────────────────────────────────────────────────────────────────────────
TEACHING_ASSIGNMENTS = {
    # Collège
    "6e M1": {
        "LIT": {"coefficient": 4, "hours": 5},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
        "TM": {"coefficient": 1, "hours": 2},
    },
    "5e M1": {
        "LIT": {"coefficient": 4, "hours": 5},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
        "TM": {"coefficient": 1, "hours": 2},
    },
    "4e A1": {
        "LIT": {"coefficient": 4, "hours": 5},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PCT": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
        "TM": {"coefficient": 1, "hours": 2},
    },
    "4e E1": {
        "LIT": {"coefficient": 4, "hours": 5},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PCT": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
        "TM": {"coefficient": 1, "hours": 2},
    },
    "3e A1": {
        "LIT": {"coefficient": 4, "hours": 5},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PCT": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
        "TM": {"coefficient": 1, "hours": 2},
    },
    "3e E1": {
        "LIT": {"coefficient": 4, "hours": 5},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PCT": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
        "TM": {"coefficient": 1, "hours": 2},
    },
    
    # Lycée
    "2nd A": {
        "LIT": {"coefficient": 4, "hours": 4},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
    },
    "2nd C": {
        "LIT": {"coefficient": 4, "hours": 4},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
    },
    "2nd TI": {
        "LIT": {"coefficient": 3, "hours": 3},
        "ANG": {"coefficient": 2, "hours": 2},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "INFO": {"coefficient": 3, "hours": 4},
        "ALGO": {"coefficient": 3, "hours": 4},
    },
    "1ère A": {
        "LIT": {"coefficient": 4, "hours": 4},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
    },
    "1ère C": {
        "LIT": {"coefficient": 4, "hours": 4},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
    },
    "1ère TI": {
        "LIT": {"coefficient": 3, "hours": 3},
        "ANG": {"coefficient": 2, "hours": 2},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "INFO": {"coefficient": 3, "hours": 4},
        "ALGO": {"coefficient": 3, "hours": 4},
        "SD": {"coefficient": 3, "hours": 3},
        "BDD": {"coefficient": 3, "hours": 3},
    },
    "1ère D": {
        "LIT": {"coefficient": 4, "hours": 4},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
    },
    "Tle A": {
        "LIT": {"coefficient": 4, "hours": 4},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
    },
    "Tle D": {
        "LIT": {"coefficient": 4, "hours": 4},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
    },
    "Tle TI": {
        "LIT": {"coefficient": 3, "hours": 3},
        "ANG": {"coefficient": 2, "hours": 2},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "INFO": {"coefficient": 3, "hours": 4},
        "ALGO": {"coefficient": 3, "hours": 4},
        "SD": {"coefficient": 3, "hours": 3},
        "BDD": {"coefficient": 3, "hours": 3},
        "RESEAUX": {"coefficient": 3, "hours": 3},
        "ARCHI": {"coefficient": 3, "hours": 3},
        "SE": {"coefficient": 3, "hours": 3},
        "GL": {"coefficient": 3, "hours": 3},
    },
    "Tle C": {
        "LIT": {"coefficient": 4, "hours": 4},
        "ANG": {"coefficient": 2, "hours": 3},
        "MATH": {"coefficient": 4, "hours": 5},
        "PC": {"coefficient": 3, "hours": 3},
        "SVT": {"coefficient": 2, "hours": 2},
        "HIST": {"coefficient": 2, "hours": 2},
        "GEO": {"coefficient": 2, "hours": 2},
        "PHILO": {"coefficient": 2, "hours": 2},
        "ECM": {"coefficient": 1, "hours": 1},
        "EPS": {"coefficient": 1, "hours": 2},
        "ARTS": {"coefficient": 1, "hours": 1},
        "MUS": {"coefficient": 1, "hours": 1},
    },
}

# ────────────────────────────────────────────────────────────────────────────────
# (Optionnel) Paramètres pour choisir l'École et l'Année Scolaire
# ────────────────────────────────────────────────────────────────────────────────
SCHOOL_ID = None       # ex: 3
SCHOOLYEAR_ID = None   # ex: 7

def pick_school_and_year():
    school = None
    year = None

    if SCHOOL_ID is not None:
        try:
            school = School.objects.get(id=SCHOOL_ID)
        except School.DoesNotExist:
            print(f"⚠️ School id={SCHOOL_ID} introuvable, passage au premier disponible…")

    if SCHOOLYEAR_ID is not None:
        try:
            year = SchoolYear.objects.get(id=SCHOOLYEAR_ID)
        except SchoolYear.DoesNotExist:
            print(f"⚠️ SchoolYear id={SCHOOLYEAR_ID} introuvable, passage au premier disponible…")

    if school is None:
        school = School.objects.first()
    if year is None:
        year = SchoolYear.objects.first()

    if not school or not year:
        print("ℹ️ Aucune School ou SchoolYear trouvée :")
        print("   → Les matières seront créées/MAJ.")
        print("   → Création des enseignants SKIPPÉE (FK obligatoires).")
    return school, year

def create_teaching_assignments(school, year, code_to_subject, teacher_by_matricule):
    """Crée les affectations d'enseignement pour toutes les classes"""
    print("\n🔗 Création des affectations d'enseignement...")
    
    created_count = 0
    updated_count = 0
    
    with transaction.atomic():
        for class_name, subjects_config in TEACHING_ASSIGNMENTS.items():
            try:
                school_class = SchoolClass.objects.get(name=class_name, year=year, school=school)
                print(f"  📚 Traitement de la classe : {class_name}")
                
                for subject_code, config in subjects_config.items():
                    subject = code_to_subject.get(subject_code)
                    if not subject:
                        print(f"    ⚠️ Matière {subject_code} introuvable, skip.")
                        continue
                    
                    # Créer l'affectation d'enseignement
                    assignment, created = TeachingAssignment.objects.get_or_create(
                        subject=subject,
                        school_class=school_class,
                        year=year,
                        defaults={
                            "coefficient": config["coefficient"],
                            "hours_per_week": config["hours"]
                        }
                    )
                    
                    if created:
                        created_count += 1
                        print(f"    ✅ Affectation créée : {subject.code} (coef: {config['coefficient']}, h: {config['hours']})")
                    else:
                        # Mettre à jour si existant
                        assignment.coefficient = config["coefficient"]
                        assignment.hours_per_week = config["hours"]
                        assignment.save()
                        updated_count += 1
                        print(f"    ♻️ Affectation MAJ : {subject.code} (coef: {config['coefficient']}, h: {config['hours']})")
                
            except SchoolClass.DoesNotExist:
                print(f"  ⚠️ Classe {class_name} introuvable, skip.")
                continue
    
    print(f"\n📊 Résumé des affectations → créées: {created_count} | mises à jour: {updated_count}")
    return created_count + updated_count

def main():
    print("🚀 Début de la création des matières et enseignants...")
    
    # ────────────────────────────────────────────────────────────────────────────────
    # Création/MAJ des matières
    # ────────────────────────────────────────────────────────────────────────────────
    print("\n📚 Création/Mise à jour des matières...")
    with transaction.atomic():
        code_to_subject = {}
        for payload in subjects_payload:
            subj, created = Subject.objects.update_or_create(
                code=payload["code"],
                defaults={
                    "name": payload["name"],
                    "description": payload.get("description", ""),
                    "group": payload["group"],
                }
            )
            code_to_subject[payload["code"]] = subj
            print(("✅ Créée" if created else "♻️ MAJ"), f"{subj.name} [{subj.code}] (Groupe {subj.group})")

    # ────────────────────────────────────────────────────────────────────────────────
    # Création d'enseignants (si School & Year dispo)
    # ────────────────────────────────────────────────────────────────────────────────
    print("\n👨‍🏫 Création des enseignants...")
    school, year = pick_school_and_year()

    if school and year:
        # Tu peux ajuster la liste (dates, villes, etc.)
        teachers_payload = [
            # Lettres / Langues
            {"matricule": "TEA001", "first_name": "Clarisse", "last_name": "Ndoumbe", "birth_date": date(1988, 4, 12), "birth_place": "Douala",   "gender": "F", "phone": "690000001", "email": "clarisse.ndoumbe@example.com", "main_subject_code": "LIT"},
            {"matricule": "TEA002", "first_name": "Williams", "last_name": "Nfor",    "birth_date": date(1985, 9, 3),  "birth_place": "Buea",     "gender": "M", "phone": "690000002", "email": "w.nfor@example.com",           "main_subject_code": "ANG"},
            # Sciences
            {"matricule": "TEA003", "first_name": "Paul",     "last_name": "Essomba", "birth_date": date(1990, 1, 23), "birth_place": "Yaoundé",  "gender": "M", "phone": "690000003", "email": "paul.essomba@example.com",     "main_subject_code": "MATH"},
            {"matricule": "TEA004", "first_name": "Aline",    "last_name": "Mbarga",  "birth_date": date(1992, 6, 2),  "birth_place": "Bafoussam","gender": "F", "phone": "690000004", "email": "aline.mbarga@example.com",     "main_subject_code": "PC"},
            {"matricule": "TEA005", "first_name": "David",    "last_name": "Nkeng",   "birth_date": date(1987, 11, 9), "birth_place": "Bamenda",  "gender": "M", "phone": "690000005", "email": "d.nkeng@example.com",          "main_subject_code": "SVT"},
            {"matricule": "TEA006", "first_name": "Sophie",   "last_name": "Tchoua",  "birth_date": date(1991, 3, 14), "birth_place": "Dschang",  "gender": "F", "phone": "690000006", "email": "s.tchoua@example.com",         "main_subject_code": "PCT"},
            {"matricule": "TEA007", "first_name": "Luc",      "last_name": "Mouafo",  "birth_date": date(1989, 8, 30), "birth_place": "Bertoua",  "gender": "M", "phone": "690000007", "email": "luc.mouafo@example.com",        "main_subject_code": "TM"},
            # TI / Informatique
            {"matricule": "TEA008", "first_name": "Nathalie", "last_name": "Abena",   "birth_date": date(1993, 5, 18), "birth_place": "Garoua",   "gender": "F", "phone": "690000008", "email": "n.abena@example.com",          "main_subject_code": "ALGO"},
            {"matricule": "TEA009", "first_name": "Eric",     "last_name": "Fouda",   "birth_date": date(1986, 12, 5), "birth_place": "Ebolowa",  "gender": "M", "phone": "690000009", "email": "eric.fouda@example.com",        "main_subject_code": "RESEAUX"},
            {"matricule": "TEA010", "first_name": "Flora",    "last_name": "Ngong",   "birth_date": date(1994, 2, 7),  "birth_place": "Maroua",   "gender": "F", "phone": "690000010", "email": "flora.ngong@example.com",       "main_subject_code": "BDD"},
            {"matricule": "TEA011", "first_name": "Patrick",  "last_name": "Nana",    "birth_date": date(1988, 10, 1), "birth_place": "Ngaoundéré","gender": "M", "phone": "690000011", "email": "patrick.nana@example.com",      "main_subject_code": "SE"},
            {"matricule": "TEA012", "first_name": "Mireille", "last_name": "Ongene",  "birth_date": date(1990, 7, 25), "birth_place": "Kribi",    "gender": "F", "phone": "690000012", "email": "mireille.ongene@example.com",   "main_subject_code": "ARCHI"},
        ]

        created_count = 0
        updated_count = 0
        teacher_objs = []

        with transaction.atomic():
            for t in teachers_payload:
                main_subj = code_to_subject.get(t["main_subject_code"])
                if not main_subj:
                    print(f"⚠️ Sujet principal {t['main_subject_code']} introuvable, saut prof {t['matricule']}")
                    continue

                obj, created = Teacher.objects.update_or_create(
                    matricule=t["matricule"],
                    defaults={
                        "first_name": t["first_name"],
                        "last_name": t["last_name"],
                        "birth_date": t["birth_date"],
                        "birth_place": t["birth_place"],
                        "gender": t["gender"],
                        "address": "",
                        "phone": t["phone"],
                        "email": t["email"],
                        "school": school,
                        "year": year,
                        "main_subject": main_subj,
                        "is_active": True,
                    }
                )
                teacher_objs.append(obj)
                created_count += 1 if created else 0
                updated_count += 0 if created else 1
                print(("👩🏽‍🏫 Créé " if created else "👨🏽‍🏫 MAJ  ") + f"{obj}  → main_subject={main_subj.code}")

        # ────────────────────────────────────────────────────────────────────────────
        # Associations M2M: lier chaque matière à 1-3 enseignants pertinents
        # ────────────────────────────────────────────────────────────────────────────
        print("\n🔗 Association des enseignants aux matières...")
        # Règle simple : on relie par proximité (ex. ALGO avec profs TI, LIT avec Clarisse, etc.)
        subject_to_teachers = {
            "LIT":   ["TEA001"],
            "ANG":   ["TEA002"],
            "MATH":  ["TEA003"],
            "PC":    ["TEA004"],
            "SVT":   ["TEA005"],
            "PCT":   ["TEA006"],
            "TM":    ["TEA007"],
            "INFO":  ["TEA008", "TEA011"],

            "HIST":  ["TEA001"],
            "GEO":   ["TEA005"],
            "PHILO": ["TEA001"],
            "ESP":   ["TEA002"],
            "ALL":   ["TEA002"],
            "ECM":   ["TEA001", "TEA005"],
            "EPS":   [],  # pas d'affectation ici, au besoin ajoute un prof d'EPS
            "ARTS":  [],
            "MUS":   [],

            "ALGO":    ["TEA008", "TEA011"],
            "SD":      ["TEA008"],
            "BDD":     ["TEA010"],
            "RESEAUX": ["TEA009"],
            "ARCHI":   ["TEA012"],
            "SE":      ["TEA011"],
            "GL":      ["TEA008", "TEA010"],
        }

        # Index rapide par matricule
        tea_by_mat = {t.matricule: t for t in teacher_objs}

        with transaction.atomic():
            for code, teacher_mats in subject_to_teachers.items():
                subj = code_to_subject.get(code)
                if not subj:
                    continue
                to_add = [tea_by_mat[m] for m in teacher_mats if m in tea_by_mat]
                if to_add:
                    subj.teachers.add(*to_add)
                    print(f"🔗 {subj.code}: +{len(to_add)} enseignant(s) liés")

        print(f"\nRésumé enseignants → créés: {created_count} | mis à jour: {updated_count}")
        
        # ────────────────────────────────────────────────────────────────────────────
        # Création des affectations d'enseignement
        # ────────────────────────────────────────────────────────────────────────────
        create_teaching_assignments(school, year, code_to_subject, tea_by_mat)
        
    else:
        print("\n⏭️ Création des enseignants non exécutée (School/SchoolYear absents).")

    print("\n🎉 Terminé : matières en place, enseignants créés/associés si possible.")

if __name__ == "__main__":
    main()
