#!/usr/bin/env python3
"""
Script de population de données scolaires
========================================

Ce script génère des données complètes pour une école secondaire camerounaise :
- Classes de la 6e à la Tle (avec spécialités A, C, TI)
- Élèves (20-40 par classe)
- Matières avec codes et spécificités TI
- Enseignants avec leurs matières
- Affectations avec coefficients et horaires
- Programmes pédagogiques
- Créneaux horaires

Usage:
    python manage.py shell < populate_school_data.py
    ou
    python populate_school_data.py (depuis le répertoire du projet)
"""

import os
import sys
import django
import random
from datetime import date, timedelta
from decimal import Decimal

# Configuration Django
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
    django.setup()

from django.db import transaction
from faker import Faker
from students.models import Student
from teachers.models import Teacher, TeachingAssignment
from subjects.models import Subject, SubjectProgram, LearningUnit
from classes.models import SchoolClass, TimetableSlot
from school.models import SchoolYear, School, SchoolLevel
from authentication.models import User

# Configuration
fake = Faker('fr_FR')
random.seed(42)  # Pour des résultats reproductibles

# Données de base pour le Cameroun
CAMEROON_CITIES = [
    'Yaoundé', 'Douala', 'Bamenda', 'Bafoussam', 'Garoua', 'Maroua', 
    'Ngaoundéré', 'Bertoua', 'Ebolowa', 'Kumba', 'Buéa', 'Limbe'
]

CAMEROON_FIRST_NAMES_M = [
    'Achille', 'Alain', 'André', 'Antoine', 'Armand', 'Bernard', 'Charles', 
    'Christian', 'Claude', 'Daniel', 'David', 'Denis', 'Dieudonné', 'Édouard',
    'Emmanuel', 'Ernest', 'Étienne', 'François', 'Georges', 'Guillaume',
    'Henri', 'Jacques', 'Jean', 'Joseph', 'Louis', 'Marc', 'Martin', 'Michel',
    'Nicolas', 'Olivier', 'Pascal', 'Patrick', 'Paul', 'Philippe', 'Pierre',
    'Raymond', 'René', 'Robert', 'Roger', 'Samuel', 'Serge', 'Simon', 'Vincent'
]

CAMEROON_FIRST_NAMES_F = [
    'Albertine', 'Alice', 'Amélie', 'Anne', 'Annie', 'Antoinette', 'Bernadette',
    'Catherine', 'Cécile', 'Charlotte', 'Christine', 'Claire', 'Claudine',
    'Colette', 'Danielle', 'Delphine', 'Diane', 'Dominique', 'Élisabeth',
    'Émilie', 'Françoise', 'Geneviève', 'Hélène', 'Isabelle', 'Jacqueline',
    'Jeanne', 'Joséphine', 'Julie', 'Louise', 'Madeleine', 'Marie', 'Martine',
    'Michelle', 'Monique', 'Nicole', 'Pascale', 'Patricia', 'Rose', 'Sylvie',
    'Thérèse', 'Véronique', 'Viviane', 'Yvonne'
]

CAMEROON_LAST_NAMES = [
    'Abanda', 'Abega', 'Abessolo', 'Aboubakari', 'Achidi', 'Achu', 'Adom',
    'Afouda', 'Ahanda', 'Aissatou', 'Akono', 'Alhadji', 'Amougou', 'Andze',
    'Angoula', 'Assiga', 'Atangana', 'Atenga', 'Awono', 'Balla', 'Bello',
    'Bengono', 'Billong', 'Biwole', 'Bouba', 'Djuikom', 'Ebanda', 'Ebogo',
    'Ekobo', 'Eloundou', 'Emane', 'Essomba', 'Etoa', 'Fouda', 'Kamga',
    'Kana', 'Kom', 'Kuete', 'Makongo', 'Manga', 'Mballa', 'Mbarga',
    'Mbengue', 'Mbia', 'Mbida', 'Mbong', 'Medjo', 'Mekongo', 'Mendomo',
    'Messi', 'Meva\'a', 'Mfomo', 'Mimba', 'Minko', 'Moukouri', 'Mvogo',
    'Ndongo', 'Nga', 'Ngah', 'Ngassam', 'Ngo', 'Ngono', 'Nguele', 'Nkomo',
    'Nkono', 'Nlate', 'Noubi', 'Ntamack', 'Ntep', 'Nyobe', 'Olinga',
    'Omgba', 'Onana', 'Onguene', 'Simo', 'Tabi', 'Tchoupe', 'Tsala',
    'Voundi', 'Wamba', 'Zang', 'Ze', 'Zemba', 'Zobo'
]

# Configuration des classes
CLASSES_CONFIG = {
    '6e': {'level': 'Sixième', 'specialties': ['M1', 'M2']},
    '5e': {'level': 'Cinquième', 'specialties': ['M1', 'M2']},
    '4e': {'level': 'Quatrième', 'specialties': ['A1', 'E1']},
    '3e': {'level': 'Troisième', 'specialties': ['E1', 'E1']},
    '2nde': {'level': 'Seconde', 'specialties': ['A', 'C', 'TI']},
    '1ère': {'level': 'Première', 'specialties': ['A', 'C', 'TI']},
    'Tle': {'level': 'Terminale', 'specialties': ['A', 'C', 'TI']},
}

# Configuration des matières
SUBJECTS_CONFIG = {
    # Matières communes à toutes les classes
    'common': [
        {'name': 'Français', 'code': 'FR', 'group': 1},
        {'name': 'Anglais', 'code': 'ANG', 'group': 1},
        {'name': 'Mathématiques', 'code': 'MATH', 'group': 2},
        {'name': 'Histoire-Géographie', 'code': 'HG', 'group': 1},
        {'name': 'Éducation Civique et Morale', 'code': 'ECM', 'group': 2},
        {'name': 'Éducation Physique et Sportive', 'code': 'EPS', 'group': 1},
    ],
    
    # Matières par niveau
    'college': [  # 6e à 3e
        {'name': 'Sciences et Vie de la Terre', 'code': 'SVT', 'group': 2},
        {'name': 'Sciences Physiques', 'code': 'PC', 'group': 2},
        {'name': 'Allemand', 'code': 'ALL', 'group': 1},
        {'name': 'Espagnol', 'code': 'ESP', 'group': 1},
        {'name': 'Arts Plastiques', 'code': 'AP', 'group': 1},
        {'name': 'Musique', 'code': 'MUS', 'group': 1},
        {'name': 'Technologie', 'code': 'TECH', 'group': 2},
        {'name': 'Informatique de Base', 'code': 'INFO_BASE', 'group': 2},
        {'name': 'Travaux Pratiques', 'code': 'TP', 'group': 2},
    ],
    
    # Matières spécifiques au lycée
    'lycee_a': [  # Littéraire
        {'name': 'Philosophie', 'code': 'PHIL', 'group': 1},
        {'name': 'Littérature', 'code': 'LIT', 'group': 1},
        {'name': 'Latin', 'code': 'LAT', 'group': 1},
        {'name': 'Grec', 'code': 'GREC', 'group': 1},
        {'name': 'Sciences Économiques et Sociales', 'code': 'SES', 'group': 1},
    ],
    
    'lycee_c': [  # Scientifique
        {'name': 'Physique-Chimie', 'code': 'PHYCHI', 'group': 2},
        {'name': 'Sciences de la Vie et de la Terre', 'code': 'SVT_LYC', 'group': 2},
        {'name': 'Sciences de l\'Ingénieur', 'code': 'SI', 'group': 2},
        {'name': 'Informatique', 'code': 'INFO', 'group': 2},
    ],
    
    'lycee_ti': [  # Technologie Informatique
        {'name': 'Algorithmique et Programmation', 'code': 'ALGO', 'group': 2},
        {'name': 'Base de Données', 'code': 'BDD', 'group': 2},
        {'name': 'Réseaux Informatiques', 'code': 'RES', 'group': 2},
        {'name': 'Systèmes d\'Exploitation', 'code': 'SE', 'group': 2},
        {'name': 'Développement Web', 'code': 'WEB', 'group': 2},
        {'name': 'Architecture des Ordinateurs', 'code': 'ARCHI', 'group': 2},
        {'name': 'Analyse et Conception', 'code': 'UML', 'group': 2},
        {'name': 'Électronique', 'code': 'ELEC', 'group': 2},
    ]
}

# Configuration des coefficients par classe et matière
COEFFICIENTS_CONFIG = {
    'college': {
        'Français': 4, 'Anglais': 3, 'Mathématiques': 4, 'Histoire-Géographie': 3,
        'Éducation Civique et Morale': 1, 'Sciences et Vie de la Terre': 2,
        'Sciences Physiques': 2, 'Éducation Physique et Sportive': 1,
        'Allemand': 2, 'Espagnol': 2, 'Arts Plastiques': 1, 'Musique': 1,
        'Technologie': 2, 'Informatique de Base': 1, 'Travaux Pratiques': 1
    },
    'lycee_a': {
        'Français': 5, 'Anglais': 3, 'Mathématiques': 2, 'Histoire-Géographie': 4,
        'Éducation Civique et Morale': 1, 'Philosophie': 4, 'Littérature': 3,
        'Latin': 2, 'Grec': 2, 'Sciences Économiques et Sociales': 3,
        'Éducation Physique et Sportive': 1
    },
    'lycee_c': {
        'Français': 3, 'Anglais': 2, 'Mathématiques': 5, 'Histoire-Géographie': 2,
        'Éducation Civique et Morale': 1, 'Physique-Chimie': 4,
        'Sciences de la Vie et de la Terre': 3, 'Sciences de l\'Ingénieur': 4,
        'Informatique': 2, 'Éducation Physique et Sportive': 1
    },
    'lycee_ti': {
        'Français': 3, 'Anglais': 2, 'Mathématiques': 4, 'Histoire-Géographie': 2,
        'Éducation Civique et Morale': 1, 'Algorithmique et Programmation': 5,
        'Base de Données': 4, 'Réseaux Informatiques': 3, 'Systèmes d\'Exploitation': 3,
        'Développement Web': 4, 'Architecture des Ordinateurs': 3,
        'Analyse et Conception': 3, 'Électronique': 2,
        'Éducation Physique et Sportive': 1
    }
}

# Configuration des heures par semaine
HOURS_CONFIG = {
    'college': {
        'Français': 5, 'Anglais': 3, 'Mathématiques': 4, 'Histoire-Géographie': 3,
        'Éducation Civique et Morale': 1, 'Sciences et Vie de la Terre': 2,
        'Sciences Physiques': 2, 'Éducation Physique et Sportive': 2,
        'Allemand': 2, 'Espagnol': 2, 'Arts Plastiques': 1, 'Musique': 1,
        'Technologie': 2, 'Informatique de Base': 1, 'Travaux Pratiques': 1
    },
    'lycee_a': {
        'Français': 6, 'Anglais': 3, 'Mathématiques': 3, 'Histoire-Géographie': 4,
        'Éducation Civique et Morale': 1, 'Philosophie': 4, 'Littérature': 3,
        'Latin': 2, 'Grec': 2, 'Sciences Économiques et Sociales': 3,
        'Éducation Physique et Sportive': 2
    },
    'lycee_c': {
        'Français': 4, 'Anglais': 3, 'Mathématiques': 6, 'Histoire-Géographie': 2,
        'Éducation Civique et Morale': 1, 'Physique-Chimie': 5,
        'Sciences de la Vie et de la Terre': 3, 'Sciences de l\'Ingénieur': 4,
        'Informatique': 2, 'Éducation Physique et Sportive': 2
    },
    'lycee_ti': {
        'Français': 4, 'Anglais': 3, 'Mathématiques': 5, 'Histoire-Géographie': 2,
        'Éducation Civique et Morale': 1, 'Algorithmique et Programmation': 6,
        'Base de Données': 4, 'Réseaux Informatiques': 3, 'Systèmes d\'Exploitation': 3,
        'Développement Web': 4, 'Architecture des Ordinateurs': 3,
        'Analyse et Conception': 3, 'Électronique': 2,
        'Éducation Physique et Sportive': 2
    }
}

def get_user():
    """Récupère ou crée un utilisateur admin pour les créations"""
    try:
        return User.objects.filter(is_superuser=True).first()
    except User.DoesNotExist:
        return None

def get_school_and_year():
    """Récupère l'école et l'année scolaire actives"""
    try:
        school = School.objects.first()
        year = SchoolYear.get_active_year()
        if not school or not year:
            print("❌ Erreur: Aucune école ou année scolaire active trouvée!")
            print("Veuillez d'abord configurer une école et une année scolaire.")
            return None, None
        return school, year
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'école/année: {e}")
        return None, None

def create_school_levels():
    """Crée les niveaux scolaires nécessaires"""
    levels = {}
    
    # Récupérer ou créer le système éducatif
    from school.models import EducationSystem
    education_system, _ = EducationSystem.objects.get_or_create(
        name="Système camerounais",
        defaults={'code': 'CAM'}
    )
    
    for class_code, config in CLASSES_CONFIG.items():
        level_name = config['level']
        level, created = SchoolLevel.objects.get_or_create(
            name=level_name,
            system=education_system,
            defaults={'order': list(CLASSES_CONFIG.keys()).index(class_code)}
        )
        levels[class_code] = level
        if created:
            print(f"✅ Niveau créé: {level_name}")
    return levels

def create_subjects():
    """Crée toutes les matières"""
    subjects = {}
    
    # Matières communes
    for subject_data in SUBJECTS_CONFIG['common']:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            defaults={
                'code': subject_data['code'],
                'group': subject_data['group']
            }
        )
        subjects[subject.name] = subject
        if created:
            print(f"✅ Matière créée: {subject.name} ({subject.code})")
    
    # Matières collège
    for subject_data in SUBJECTS_CONFIG['college']:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            defaults={
                'code': subject_data['code'],
                'group': subject_data['group']
            }
        )
        subjects[subject.name] = subject
        if created:
            print(f"✅ Matière créée: {subject.name} ({subject.code})")
    
    # Matières lycée A
    for subject_data in SUBJECTS_CONFIG['lycee_a']:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            defaults={
                'code': subject_data['code'],
                'group': subject_data['group']
            }
        )
        subjects[subject.name] = subject
        if created:
            print(f"✅ Matière créée: {subject.name} ({subject.code})")
    
    # Matières lycée C
    for subject_data in SUBJECTS_CONFIG['lycee_c']:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            defaults={
                'code': subject_data['code'],
                'group': subject_data['group']
            }
        )
        subjects[subject.name] = subject
        if created:
            print(f"✅ Matière créée: {subject.name} ({subject.code})")
    
    # Matières TI
    for subject_data in SUBJECTS_CONFIG['lycee_ti']:
        subject, created = Subject.objects.get_or_create(
            name=subject_data['name'],
            defaults={
                'code': subject_data['code'],
                'group': subject_data['group']
            }
        )
        subjects[subject.name] = subject
        if created:
            print(f"✅ Matière créée: {subject.name} ({subject.code})")
    
    return subjects

def create_classes(school, year, levels):
    """Crée toutes les classes"""
    classes = []
    
    for class_code, config in CLASSES_CONFIG.items():
        level = levels[class_code]
        specialties = config['specialties']
        
        if specialties == ['']:  # Pas de spécialité
            class_name = class_code
            school_class, created = SchoolClass.objects.get_or_create(
                name=class_name,
                level=level,
                year=year,
                school=school,
                defaults={
                    'capacity': 45,
                    'is_active': True,
                    'created_by': get_user()
                }
            )
            classes.append(school_class)
            if created:
                print(f"✅ Classe créée: {class_name}")
        else:
            for specialty in specialties:
                class_name = f"{class_code} {specialty}"
                school_class, created = SchoolClass.objects.get_or_create(
                    name=class_name,
                    level=level,
                    year=year,
                    school=school,
                    defaults={
                        'capacity': 40,
                        'is_active': True,
                        'created_by': get_user()
                    }
                )
                classes.append(school_class)
                if created:
                    print(f"✅ Classe créée: {class_name}")
    
    return classes

def generate_matricule(type_prefix, year, index):
    """Génère un matricule unique"""
    year_suffix = str(year.annee)[-2:]
    return f"{type_prefix}{year_suffix}{index:04d}"

def create_teachers(school, year, subjects):
    """Crée les enseignants"""
    teachers = []
    subject_list = list(subjects.values())
    
    # Calculer le nombre d'enseignants nécessaires
    num_teachers = 45  # Environ 45 enseignants pour couvrir toutes les matières
    
    for i in range(num_teachers):
        gender = random.choice(['M', 'F'])
        
        if gender == 'M':
            first_name = random.choice(CAMEROON_FIRST_NAMES_M)
        else:
            first_name = random.choice(CAMEROON_FIRST_NAMES_F)
        
        last_name = random.choice(CAMEROON_LAST_NAMES)
        
        # Générer une date de naissance (25-60 ans)
        birth_year = random.randint(1964, 1999)
        birth_date = fake.date_between(
            start_date=date(birth_year, 1, 1),
            end_date=date(birth_year, 12, 31)
        )
        
        # Matricule enseignant
        matricule = generate_matricule('ENS', year, i + 1)
        
        # Sélectionner une matière principale
        main_subject = random.choice(subject_list)
        
        teacher, created = Teacher.objects.get_or_create(
            matricule=matricule,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'birth_date': birth_date,
                'birth_place': random.choice(CAMEROON_CITIES),
                'gender': gender,
                'nationality': 'Camerounaise',
                'address': fake.address(),
                'phone': f"+237{random.randint(600000000, 699999999)}",
                'email': f"{first_name.lower()}.{last_name.lower()}@school.cm",
                'school': school,
                'year': year,
                'main_subject': main_subject,
                'is_active': True,
                'created_by': get_user()
            }
        )
        
        if created:
            # Affecter 2-4 matières à l'enseignant
            num_subjects = random.randint(2, 4)
            teacher_subjects = random.sample(subject_list, num_subjects)
            
            # S'assurer que la matière principale est incluse
            if main_subject not in teacher_subjects:
                teacher_subjects[0] = main_subject
            
            teacher.subjects.set(teacher_subjects)
            teachers.append(teacher)
            
            subject_names = ", ".join([s.name for s in teacher_subjects])
            print(f"✅ Enseignant créé: {teacher} (Matières: {subject_names})")
    
    return teachers

def create_students(school, year, classes):
    """Crée les élèves pour toutes les classes"""
    students = []
    
    for school_class in classes:
        # Nombre aléatoire d'élèves entre 20 et 40
        num_students = random.randint(20, 40)
        
        for i in range(num_students):
            gender = random.choice(['M', 'F'])
            
            if gender == 'M':
                first_name = random.choice(CAMEROON_FIRST_NAMES_M)
            else:
                first_name = random.choice(CAMEROON_FIRST_NAMES_F)
            
            last_name = random.choice(CAMEROON_LAST_NAMES)
            
            # Âge approprié selon la classe
            base_ages = {
                '6e': 11, '5e': 12, '4e': 13, '3e': 14,
                '2nde': 15, '1ère': 16, 'Tle': 17
            }
            
            # Extraire le niveau de base de la classe
            class_base = school_class.name.split()[0]
            base_age = base_ages.get(class_base, 15)
            
            # Variation d'âge (±2 ans)
            age = base_age + random.randint(-2, 2)
            birth_year = 2024 - age
            
            birth_date = fake.date_between(
                start_date=date(birth_year, 1, 1),
                end_date=date(birth_year, 12, 31)
            )
            
            # Matricule élève
            matricule = generate_matricule('STU', year, len(students) + 1)
            
            student, created = Student.objects.get_or_create(
                matricule=matricule,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'birth_date': birth_date,
                    'birth_place': random.choice(CAMEROON_CITIES),
                    'gender': gender,
                    'nationality': 'Camerounaise',
                    'address': fake.address(),
                    'phone': f"+237{random.randint(600000000, 699999999)}",
                    'current_class': school_class,
                    'year': year,
                    'school': school,
                    'is_active': True,
                    'is_repeating': random.choice([True, False]) if random.random() < 0.05 else False,
                    'created_by': get_user()
                }
            )
            
            if created:
                students.append(student)
        
        print(f"✅ {num_students} élèves créés pour la classe {school_class.name}")
    
    return students

def get_class_subjects(class_name, subjects):
    """Retourne les matières pour une classe donnée"""
    class_subjects = []
    
    # Matières communes à TOUTES les classes
    common_subjects = ['Français', 'Anglais', 'Mathématiques', 'Histoire-Géographie', 
                      'Éducation Civique et Morale', 'Éducation Physique et Sportive']
    for subject_name in common_subjects:
        if subject_name in subjects:
            class_subjects.append(subjects[subject_name])
    
    # Matières selon le niveau - TOUTES les matières du programme
    if any(x in class_name for x in ['6e', '5e', '4e', '3e']):  # Collège
        # TOUTES les matières du collège (programme officiel)
        college_subjects = ['Sciences et Vie de la Terre', 'Sciences Physiques', 
                          'Allemand', 'Espagnol', 'Arts Plastiques', 'Musique', 'Technologie',
                          'Informatique de Base', 'Travaux Pratiques']
        for subject_name in college_subjects:
            if subject_name in subjects:
                class_subjects.append(subjects[subject_name])
    
    elif 'A' in class_name:  # Littéraire
        # TOUTES les matières du lycée littéraire
        lycee_a_subjects = ['Philosophie', 'Littérature', 'Latin', 'Grec', 
                           'Sciences Économiques et Sociales']
        for subject_name in lycee_a_subjects:
            if subject_name in subjects:
                class_subjects.append(subjects[subject_name])
    
    elif 'C' in class_name:  # Scientifique
        # TOUTES les matières du lycée scientifique
        lycee_c_subjects = ['Physique-Chimie', 'Sciences de la Vie et de la Terre', 
                           'Sciences de l\'Ingénieur', 'Informatique']
        for subject_name in lycee_c_subjects:
            if subject_name in subjects:
                class_subjects.append(subjects[subject_name])
    
    elif 'TI' in class_name:  # Technologie Informatique
        # TOUTES les matières spécialisées en TI
        lycee_ti_subjects = ['Algorithmique et Programmation', 'Base de Données', 
                            'Réseaux Informatiques', 'Systèmes d\'Exploitation',
                            'Développement Web', 'Architecture des Ordinateurs',
                            'Analyse et Conception', 'Électronique']
        for subject_name in lycee_ti_subjects:
            if subject_name in subjects:
                class_subjects.append(subjects[subject_name])
    
    return class_subjects

def get_coeff_and_hours(class_name, subject_name):
    """Retourne le coefficient et les heures pour une matière dans une classe"""
    if any(x in class_name for x in ['6e', '5e', '4e', '3e']):
        coeff_config = COEFFICIENTS_CONFIG['college']
        hours_config = HOURS_CONFIG['college']
    elif 'A' in class_name:
        coeff_config = COEFFICIENTS_CONFIG['lycee_a']
        hours_config = HOURS_CONFIG['lycee_a']
    elif 'C' in class_name:
        coeff_config = COEFFICIENTS_CONFIG['lycee_c']
        hours_config = HOURS_CONFIG['lycee_c']
    elif 'TI' in class_name:
        coeff_config = COEFFICIENTS_CONFIG['lycee_ti']
        hours_config = HOURS_CONFIG['lycee_ti']
    else:
        coeff_config = COEFFICIENTS_CONFIG['college']
        hours_config = HOURS_CONFIG['college']
    
    coefficient = coeff_config.get(subject_name, 1)
    hours = hours_config.get(subject_name, 2)
    
    return coefficient, hours

def create_teaching_assignments(classes, teachers, subjects, year):
    """Crée les affectations d'enseignement"""
    assignments = []
    
    for school_class in classes:
        class_subjects = get_class_subjects(school_class.name, subjects)
        
        # Assigner un professeur titulaire
        main_teacher = random.choice(teachers)
        school_class.main_teacher = main_teacher
        school_class.save()
        
        for subject in class_subjects:
            # Trouver des enseignants qualifiés pour cette matière
            qualified_teachers = [t for t in teachers if subject in t.subjects.all()]
            
            if qualified_teachers:
                teacher = random.choice(qualified_teachers)
            else:
                # Si aucun enseignant qualifié, prendre un enseignant au hasard
                teacher = random.choice(teachers)
                teacher.subjects.add(subject)
            
            # Obtenir coefficient et heures
            coefficient, hours = get_coeff_and_hours(school_class.name, subject.name)
            
            assignment, created = TeachingAssignment.objects.get_or_create(
                teacher=teacher,
                subject=subject,
                school_class=school_class,
                year=year,
                defaults={
                    'coefficient': coefficient,
                    'hours_per_week': hours
                }
            )
            
            if created:
                assignments.append(assignment)
        
        print(f"✅ Affectations créées pour {school_class.name} (Titulaire: {main_teacher})")
    
    return assignments

def create_subject_programs(classes, subjects, year):
    """Crée les programmes pédagogiques"""
    programs = []
    
    for school_class in classes:
        class_subjects = get_class_subjects(school_class.name, subjects)
        
        for subject in class_subjects:
            # Créer un programme basique
            title = f"Programme {subject.name} - {school_class.name}"
            
            program, created = SubjectProgram.objects.get_or_create(
                subject=subject,
                school_class=school_class,
                school_year=year,
                defaults={
                    'title': title,
                    'description': f"Programme pédagogique de {subject.name} pour la classe {school_class.name}",
                    'objectives': f"Objectifs d'apprentissage pour {subject.name} en {school_class.name}",
                    'total_hours': get_coeff_and_hours(school_class.name, subject.name)[1] * 30,  # ~30 semaines
                    'difficulty_level': 'INTERMEDIATE',
                    'is_active': True,
                    'is_approved': True
                }
            )
            
            if created:
                programs.append(program)
                
                # Créer quelques unités d'apprentissage
                for i in range(3, 7):  # 3 à 6 unités par programme
                    unit_title = f"Unité {i} - {subject.name}"
                    
                    LearningUnit.objects.create(
                        subject_program=program,
                        title=unit_title,
                        description=f"Description de l'unité {i} pour {subject.name}",
                        estimated_hours=random.randint(8, 16),
                        order=i,
                        key_concepts=f"Concepts clés de l'unité {i}",
                        skills_developed=f"Compétences développées dans l'unité {i}",
                        learning_objectives=f"Objectifs spécifiques de l'unité {i}",
                        is_active=True
                    )
        
        print(f"✅ Programmes créés pour {school_class.name}")
    
    return programs

def create_timetable_slots(classes, teachers, subjects, year):
    """Crée quelques créneaux horaires d'exemple"""
    slots = []
    
    for school_class in classes:
        class_subjects = get_class_subjects(school_class.name, subjects)
        
        # Créer quelques créneaux pour chaque jour de la semaine
        for day in range(1, 6):  # Lundi à Vendredi
            daily_subjects = random.sample(class_subjects, min(6, len(class_subjects)))
            
            for period, subject in enumerate(daily_subjects, 1):
                # Trouver un enseignant pour cette matière
                qualified_teachers = [t for t in teachers if subject in t.subjects.all()]
                
                if qualified_teachers:
                    teacher = random.choice(qualified_teachers)
                else:
                    teacher = random.choice(teachers)
                
                slot, created = TimetableSlot.objects.get_or_create(
                    class_obj=school_class,
                    year=year,
                    day=day,
                    period=period,
                    defaults={
                        'subject': subject,
                        'teacher': teacher,
                        'duration': 1
                    }
                )
                
                if created:
                    slots.append(slot)
        
        print(f"✅ Créneaux horaires créés pour {school_class.name}")
    
    return slots

@transaction.atomic
def populate_all_data():
    """Fonction principale pour peupler toutes les données"""
    print("🚀 Début de la population des données scolaires...")
    print("=" * 60)
    
    # Vérifications préliminaires
    school, year = get_school_and_year()
    if not school or not year:
        return
    
    print(f"📚 École: {school.name}")
    print(f"📅 Année scolaire: {year.annee}")
    print("-" * 60)
    
    try:
        # 1. Créer les niveaux scolaires
        print("📝 1. Création des niveaux scolaires...")
        levels = create_school_levels()
        
        # 2. Créer les matières
        print("\n📚 2. Création des matières...")
        subjects = create_subjects()
        
        # 3. Créer les classes
        print("\n🏫 3. Création des classes...")
        classes = create_classes(school, year, levels)
        
        # 4. Créer les enseignants
        print("\n👨‍🏫 4. Création des enseignants...")
        teachers = create_teachers(school, year, subjects)
        
        # 5. Créer les élèves
        print("\n👨‍🎓 5. Création des élèves...")
        students = create_students(school, year, classes)
        
        # 6. Créer les affectations d'enseignement
        print("\n📋 6. Création des affectations d'enseignement...")
        assignments = create_teaching_assignments(classes, teachers, subjects, year)
        
        # 7. Créer les programmes pédagogiques
        print("\n📖 7. Création des programmes pédagogiques...")
        programs = create_subject_programs(classes, subjects, year)
        
        # 8. Créer quelques créneaux horaires
        print("\n⏰ 8. Création des créneaux horaires...")
        slots = create_timetable_slots(classes, teachers, subjects, year)
        
        print("\n" + "=" * 60)
        print("✅ POPULATION TERMINÉE AVEC SUCCÈS!")
        print("=" * 60)
        print(f"📊 Résumé:")
        print(f"   • Niveaux scolaires: {len(levels)}")
        print(f"   • Matières: {len(subjects)}")
        print(f"   • Classes: {len(classes)}")
        print(f"   • Enseignants: {len(teachers)}")
        print(f"   • Élèves: {len(students)}")
        print(f"   • Affectations: {len(assignments)}")
        print(f"   • Programmes: {len(programs)}")
        print(f"   • Créneaux horaires: {len(slots)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la population: {e}")
        print("La transaction a été annulée.")
        raise

if __name__ == "__main__":
    populate_all_data()
