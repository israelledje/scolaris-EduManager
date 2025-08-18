#!/usr/bin/env python
"""
Script de création de données d'exemple pour le système pédagogique SCOLARIS
Génère des programmes pédagogiques complets pour la classe 6e M1
AVEC DES HORAIRES RÉALISTES (36h/semaine maximum)
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.db.models import Q
from authentication.models import User
from subjects.models import Subject, SubjectProgram, LearningUnit, Lesson, LessonProgress
from classes.models import SchoolClass, TimetableSlot
from school.models import SchoolYear
from students.models import Student
from teachers.models import Teacher

def create_sample_data():
    """Crée des données d'exemple pour le système pédagogique avec des horaires réalistes"""
    
    print("🎓 Création des données d'exemple pour le système pédagogique SCOLARIS")
    print("📅 AVEC DES HORAIRES RÉALISTES (36h/semaine maximum)")
    print("=" * 70)
    
    # Récupération des données existantes
    try:
        # Récupérer la classe 6e M1
        school_class = SchoolClass.objects.get(name='6e M1')
        print(f"✅ Classe trouvée: {school_class.name}")
        
        # Récupérer l'année scolaire actuelle
        current_year = SchoolYear.get_active_year()
        if not current_year:
            current_year = SchoolYear.objects.first()
        print(f"✅ Année scolaire: {current_year}")
        
        # Récupérer les enseignants
        teachers = Teacher.objects.all()
        if not teachers.exists():
            print("❌ Aucun enseignant trouvé. Créez d'abord des enseignants.")
            return
        print(f"✅ {teachers.count()} enseignant(s) trouvé(s)")
        
        # Récupérer les matières existantes ou en créer de nouvelles
        subjects_data = [
            {
                'name': 'Mathématiques',
                'code': 'MATH',
                'description': 'Mathématiques niveau 6e - Algèbre, géométrie, arithmétique'
            },
            {
                'name': 'Français',
                'code': 'FRAN',
                'description': 'Français niveau 6e - Grammaire, conjugaison, lecture, expression'
            },
            {
                'name': 'Histoire-Géographie',
                'code': 'HIST',
                'description': 'Histoire et géographie niveau 6e - Antiquité, monde moderne'
            },
            {
                'name': 'Sciences et Technologie',
                'code': 'SCIE',
                'description': 'Sciences et technologie niveau 6e - SVT, physique, chimie'
            },
            {
                'name': 'Anglais',
                'code': 'ANGL',
                'description': 'Anglais niveau 6e - Communication, grammaire, vocabulaire'
            },
            {
                'name': 'Arts Plastiques',
                'code': 'ARTS',
                'description': 'Arts plastiques niveau 6e - Créativité, techniques, histoire de l\'art'
            },
            {
                'name': 'Éducation Physique et Sportive',
                'code': 'EPS',
                'description': 'EPS niveau 6e - Développement physique, sports collectifs et individuels'
            },
            {
                'name': 'Technologie',
                'code': 'TECH',
                'description': 'Technologie niveau 6e - Conception, fabrication, informatique'
            }
        ]
        
        subjects = []
        for subject_data in subjects_data:
            # Vérifier si la matière existe déjà par code ou par nom
            existing_subject = Subject.objects.filter(
                Q(code=subject_data['code']) | Q(name=subject_data['name'])
            ).first()
            
            if existing_subject:
                print(f"✅ Matière existante: {existing_subject.name}")
                subjects.append(existing_subject)
            else:
                try:
                    subject = Subject.objects.create(**subject_data)
                    print(f"✅ Matière créée: {subject.name}")
                    subjects.append(subject)
                except Exception as e:
                    print(f"⚠️ Erreur lors de la création de {subject_data['name']}: {e}")
                    # Essayer de récupérer une matière existante similaire
                    similar_subject = Subject.objects.filter(
                        name__icontains=subject_data['name'][:5]
                    ).first()
                    if similar_subject:
                        print(f"   → Utilisation de la matière similaire: {similar_subject.name}")
                        subjects.append(similar_subject)
                    else:
                        print(f"   → Impossible de créer ou récupérer la matière {subject_data['name']}")
                        continue
        
        # Utiliser un enseignant existant pour créer les programmes
        admin_teacher = teachers.first()
        if admin_teacher:
            print(f"✅ Enseignant sélectionné pour la création: {admin_teacher.first_name} {admin_teacher.last_name}")
        else:
            print("❌ Aucun enseignant disponible pour créer les programmes")
            return
        
        # PROGRAMMES PÉDAGOGIQUES AVEC HORAIRES RÉALISTES
        # Total: 36h/semaine (respect de la limite scolaire)
        programs_data = [
            {
                'subject': 'Mathématiques',
                'title': 'Programme Mathématiques 6e M1 - Fondamentaux',
                'description': 'Programme complet de mathématiques pour la 6e M1 couvrant les bases essentielles',
                'objectives': '• Maîtriser les opérations de base\n• Comprendre la géométrie plane\n• Résoudre des problèmes simples\n• Développer le raisonnement logique',
                'total_hours': 5,  # 5h/semaine (réaliste pour les maths)
                'difficulty_level': 'DEBUTANT',
                'units': [
                    {
                        'title': 'Les Nombres Entiers',
                        'description': 'Apprentissage des nombres entiers, opérations de base et résolution de problèmes',
                        'estimated_hours': 2,
                        'order': 1,
                        'key_concepts': 'Nombres entiers, addition, soustraction, multiplication, division',
                        'skills_developed': 'Calcul mental, résolution de problèmes, logique mathématique',
                        'learning_objectives': '• Comprendre la valeur des chiffres\n• Maîtriser les 4 opérations\n• Résoudre des problèmes simples',
                        'lessons': [
                            {
                                'title': 'Introduction aux nombres entiers',
                                'objectives': 'Découverte des nombres entiers, lecture et écriture',
                                'activities': 'Exercices de lecture de nombres, jeux de cartes numériques',
                                'materials_needed': 'Cartes numériques, tableau, manuel',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            },
                            {
                                'title': 'L\'addition des nombres entiers',
                                'objectives': 'Techniques d\'addition, propriétés commutatives et associatives',
                                'activities': 'Exercices pratiques, problèmes concrets',
                                'materials_needed': 'Calculatrice, feuilles d\'exercices',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    },
                    {
                        'title': 'La Géométrie Plane',
                        'description': 'Étude des figures géométriques de base et de leurs propriétés',
                        'estimated_hours': 2,
                        'order': 2,
                        'key_concepts': 'Points, droites, segments, angles, polygones',
                        'skills_developed': 'Construction géométrique, mesure, observation',
                        'learning_objectives': '• Reconnaître les figures géométriques\n• Construire des figures simples\n• Mesurer des angles et segments',
                        'lessons': [
                            {
                                'title': 'Les figures de base',
                                'objectives': 'Découverte des points, droites et segments',
                                'activities': 'Construction au compas et à la règle, identification',
                                'materials_needed': 'Compas, règle, crayon, feuilles',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    }
                ]
            },
            {
                'subject': 'Français',
                'title': 'Programme Français 6e M1 - Communication et Expression',
                'description': 'Programme de français axé sur la maîtrise de la langue et l\'expression',
                'objectives': '• Améliorer la lecture et la compréhension\n• Maîtriser la grammaire de base\n• Développer l\'expression écrite et orale\n• Découvrir la littérature',
                'total_hours': 5,  # 5h/semaine (réaliste pour le français)
                'difficulty_level': 'DEBUTANT',
                'units': [
                    {
                        'title': 'Grammaire et Conjugaison',
                        'description': 'Apprentissage des règles grammaticales et des temps verbaux',
                        'estimated_hours': 3,
                        'order': 1,
                        'key_concepts': 'Classes grammaticales, conjugaison, accords',
                        'skills_developed': 'Analyse grammaticale, expression correcte',
                        'learning_objectives': '• Identifier les classes de mots\n• Conjuguer les verbes du 1er groupe\n• Respecter les accords',
                        'lessons': [
                            {
                                'title': 'Les classes de mots',
                                'objectives': 'Découverte des noms, verbes, adjectifs et déterminants',
                                'activities': 'Exercices de classification, jeux de mots',
                                'materials_needed': 'Manuel, fiches d\'exercices, tableau',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    }
                ]
            },
            {
                'subject': 'Histoire-Géographie',
                'title': 'Programme Histoire-Géo 6e M1 - Découverte du Monde',
                'description': 'Programme d\'histoire et géographie pour comprendre le monde',
                'objectives': '• Découvrir l\'histoire ancienne\n• Comprendre la géographie du monde\n• Développer l\'esprit critique\n• Acquérir des repères temporels et spatiaux',
                'total_hours': 4,  # 4h/semaine (réaliste pour l'histoire-géo)
                'difficulty_level': 'DEBUTANT',
                'units': [
                    {
                        'title': 'L\'Antiquité',
                        'description': 'Étude des civilisations anciennes et de leur héritage',
                        'estimated_hours': 2,
                        'order': 1,
                        'key_concepts': 'Civilisations antiques, héritage culturel, chronologie',
                        'skills_developed': 'Analyse historique, compréhension du temps',
                        'learning_objectives': '• Connaître les grandes civilisations\n• Comprendre l\'héritage antique\n• Se repérer dans le temps',
                        'lessons': [
                            {
                                'title': 'Introduction à l\'Antiquité',
                                'objectives': 'Définition de l\'Antiquité, chronologie générale',
                                'activities': 'Frise chronologique, lecture de documents',
                                'materials_needed': 'Frise chronologique, documents historiques',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    }
                ]
            },
            {
                'subject': 'Sciences et Technologie',
                'title': 'Programme Sciences 6e M1 - Découverte Scientifique',
                'description': 'Programme de sciences pour éveiller la curiosité scientifique',
                'objectives': '• Découvrir le monde vivant\n• Comprendre les phénomènes naturels\n• Développer l\'esprit scientifique\n• Pratiquer la démarche expérimentale',
                'total_hours': 4,  # 4h/semaine (réaliste pour les sciences)
                'difficulty_level': 'DEBUTANT',
                'units': [
                    {
                        'title': 'Le Monde Vivant',
                        'description': 'Découverte de la diversité du monde vivant',
                        'estimated_hours': 2,
                        'order': 1,
                        'key_concepts': 'Biodiversité, classification, écosystèmes',
                        'skills_developed': 'Observation, classification, démarche scientifique',
                        'learning_objectives': '• Observer la diversité du vivant\n• Classer les êtres vivants\n• Comprendre les écosystèmes',
                        'lessons': [
                            {
                                'title': 'Qu\'est-ce que le vivant ?',
                                'objectives': 'Caractéristiques des êtres vivants',
                                'activities': 'Observation d\'échantillons, expériences',
                                'materials_needed': 'Microscopes, échantillons, loupes',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    }
                ]
            },
            {
                'subject': 'Anglais',
                'title': 'Programme Anglais 6e M1 - Premiers Pas',
                'description': 'Programme d\'anglais pour débutants, communication de base',
                'objectives': '• Acquérir le vocabulaire de base\n• Maîtriser les structures simples\n• Communiquer dans des situations quotidiennes\n• Découvrir la culture anglophone',
                'total_hours': 3,  # 3h/semaine (réaliste pour l'anglais)
                'difficulty_level': 'DEBUTANT',
                'units': [
                    {
                        'title': 'Se Présenter',
                        'description': 'Apprendre à se présenter et à présenter les autres',
                        'estimated_hours': 2,
                        'order': 1,
                        'key_concepts': 'Pronoms personnels, verbes être et avoir, questions',
                        'skills_developed': 'Communication orale, compréhension, expression',
                        'learning_objectives': '• Se présenter en anglais\n• Poser des questions simples\n• Comprendre une présentation',
                        'lessons': [
                            {
                                'title': 'Hello, my name is...',
                                'objectives': 'Formules de présentation, pronoms personnels',
                                'activities': 'Dialogues, jeux de rôle, chansons',
                                'materials_needed': 'CD audio, images, flashcards',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    }
                ]
            },
            {
                'subject': 'Arts Plastiques',
                'title': 'Programme Arts 6e M1 - Créativité et Expression',
                'description': 'Programme d\'arts plastiques pour développer la créativité',
                'objectives': '• Développer la créativité artistique\n• Découvrir les techniques plastiques\n• Comprendre l\'histoire de l\'art\n• S\'exprimer par l\'art',
                'total_hours': 2,  # 2h/semaine (réaliste pour les arts)
                'difficulty_level': 'DEBUTANT',
                'units': [
                    {
                        'title': 'Les Couleurs et Formes',
                        'description': 'Découverte des couleurs primaires et des formes géométriques',
                        'estimated_hours': 2,
                        'order': 1,
                        'key_concepts': 'Couleurs primaires, formes géométriques, composition',
                        'skills_developed': 'Créativité, technique picturale, observation',
                        'learning_objectives': '• Reconnaître les couleurs primaires\n• Créer des compositions\n• Utiliser différentes techniques',
                        'lessons': [
                            {
                                'title': 'Découverte des couleurs',
                                'objectives': 'Les couleurs primaires et secondaires, mélanges',
                                'activities': 'Mélanges de couleurs, peinture, collage',
                                'materials_needed': 'Peintures, pinceaux, papiers, palettes',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    }
                ]
            },
            {
                'subject': 'Éducation Physique et Sportive',
                'title': 'Programme EPS 6e M1 - Développement Physique',
                'description': 'Programme d\'EPS pour le développement physique et sportif',
                'objectives': '• Développer les capacités physiques\n• Pratiquer des sports collectifs\n• Apprendre la coopération\n• Respecter les règles',
                'total_hours': 4,  # 4h/semaine (réaliste pour l'EPS)
                'difficulty_level': 'DEBUTANT',
                'units': [
                    {
                        'title': 'Sports Collectifs',
                        'description': 'Apprentissage des sports collectifs de base',
                        'estimated_hours': 2,
                        'order': 1,
                        'key_concepts': 'Coopération, règles, fair-play',
                        'skills_developed': 'Coordination, esprit d\'équipe, motricité',
                        'learning_objectives': '• Comprendre les règles du jeu\n• Coopérer avec les autres\n• Respecter l\'adversaire',
                        'lessons': [
                            {
                                'title': 'Initiation au handball',
                                'objectives': 'Règles de base, passes et tirs',
                                'activities': 'Exercices techniques, matchs',
                                'materials_needed': 'Ballons, plots, filets',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    }
                ]
            },
            {
                'subject': 'Technologie',
                'title': 'Programme Technologie 6e M1 - Innovation et Création',
                'description': 'Programme de technologie pour découvrir l\'innovation',
                'objectives': '• Découvrir les objets techniques\n• Comprendre la conception\n• Utiliser l\'informatique\n• Créer des projets',
                'total_hours': 2,  # 2h/semaine (réaliste pour la technologie)
                'difficulty_level': 'DEBUTANT',
                'units': [
                    {
                        'title': 'Les Objets Techniques',
                        'description': 'Découverte et analyse d\'objets techniques',
                        'estimated_hours': 2,
                        'order': 1,
                        'key_concepts': 'Fonction, structure, matériaux',
                        'skills_developed': 'Analyse technique, créativité, informatique',
                        'learning_objectives': '• Analyser un objet technique\n• Comprendre sa fonction\n• Identifier ses composants',
                        'lessons': [
                            {
                                'title': 'Qu\'est-ce qu\'un objet technique ?',
                                'objectives': 'Définition et analyse d\'objets techniques',
                                'activities': 'Observation, dessin technique, informatique',
                                'materials_needed': 'Objets techniques, ordinateurs, logiciels',
                                'planned_duration': 55,
                                'status': 'PLANNED'
                            }
                        ]
                    }
                ]
            }
        ]
        
        # Vérification du total des heures
        total_hours = sum(program['total_hours'] for program in programs_data)
        print(f"\n📊 VÉRIFICATION DES HORAIRES:")
        print(f"   • Total des heures demandées: {total_hours}h/semaine")
        print(f"   • Limite scolaire: 36h/semaine")
        
        if total_hours > 36:
            print(f"   ⚠️  ATTENTION: Total dépassant la limite de 36h/semaine")
            print(f"   • Les heures seront automatiquement ajustées lors de la génération de l'emploi du temps")
        elif total_hours < 36:
            print(f"   ℹ️  Total sous la limite: {36 - total_hours}h disponibles")
        else:
            print(f"   ✅ Total parfait: exactement 36h/semaine")
        
        # Suppression des programmes existants pour cette classe et cette année
        print("\n🧹 Suppression des programmes existants...")
        existing_programs = SubjectProgram.objects.filter(
            school_class=school_class,
            school_year=current_year
        )
        if existing_programs.exists():
            count = existing_programs.count()
            existing_programs.delete()
            print(f"✅ {count} programme(s) existant(s) supprimé(s)")
        else:
            print("✅ Aucun programme existant à supprimer")
        
        # Suppression des créneaux horaires existants pour cette classe et cette année
        print("🧹 Suppression des créneaux horaires existants...")
        existing_slots = TimetableSlot.objects.filter(
            class_obj=school_class,
            year=current_year
        )
        if existing_slots.exists():
            count = existing_slots.count()
            existing_slots.delete()
            print(f"✅ {count} créneau(x) horaire(s) supprimé(s)")
        else:
            print("✅ Aucun créneau horaire existant à supprimer")
        
        # Création des programmes pédagogiques
        created_programs = []
        
        for program_data in programs_data:
            # Trouver la matière correspondante
            subject = next((s for s in subjects if s.name == program_data['subject']), None)
            if not subject:
                print(f"❌ Matière non trouvée: {program_data['subject']}")
                continue
            
            # Créer le programme
            program = SubjectProgram.objects.create(
                subject=subject,
                school_class=school_class,
                school_year=current_year,
                title=program_data['title'],
                description=program_data['description'],
                objectives=program_data['objectives'],
                total_hours=program_data['total_hours'],
                difficulty_level=program_data['difficulty_level'],
                is_active=True,
                is_approved=True,
                created_by=admin_teacher
            )
            print(f"✅ Programme créé: {program.title} ({program.total_hours}h/semaine)")
            
            created_programs.append(program)
            
            # Créer les unités d'apprentissage
            for unit_data in program_data['units']:
                unit = LearningUnit.objects.create(
                    subject_program=program,
                    title=unit_data['title'],
                    description=unit_data['description'],
                    estimated_hours=unit_data['estimated_hours'],
                    order=unit_data['order'],
                    key_concepts=unit_data['key_concepts'],
                    skills_developed=unit_data['skills_developed'],
                    learning_objectives=unit_data['learning_objectives'],
                    is_active=True
                )
                print(f"  ✅ Unité créée: {unit.title} ({unit.estimated_hours}h)")
                
                # Créer les leçons
                for lesson_data in unit_data['lessons']:
                    # Assigner un enseignant aléatoirement
                    teacher = random.choice(teachers)
                    
                    # Créer une date planifiée (dans les 2 prochaines semaines)
                    planned_date = datetime.now().date() + timedelta(days=random.randint(1, 14))
                    
                    lesson = Lesson.objects.create(
                        learning_unit=unit,
                        title=lesson_data['title'],
                        objectives=lesson_data['objectives'],
                        activities=lesson_data['activities'],
                        materials_needed=lesson_data['materials_needed'],
                        planned_date=planned_date,
                        planned_duration=lesson_data['planned_duration'],
                        teacher=teacher,
                        status=lesson_data['status']
                    )
                    print(f"    ✅ Leçon créée: {lesson.title} (Prof: {teacher.first_name} {teacher.last_name})")
        
        print("\n" + "=" * 70)
        print("🎉 CRÉATION TERMINÉE AVEC SUCCÈS!")
        print(f"📊 Résumé:")
        print(f"   • {len(created_programs)} programmes pédagogiques créés")
        print(f"   • {LearningUnit.objects.filter(subject_program__in=created_programs).count()} unités d'apprentissage")
        print(f"   • {Lesson.objects.filter(learning_unit__subject_program__in=created_programs).count()} leçons")
        print(f"   • Total des heures: {total_hours}h/semaine")
        print(f"   • Classe: {school_class.name}")
        print(f"   • Année: {current_year}")
        print("\n🚀 Vous pouvez maintenant:")
        print(f"   • Accéder au tableau de bord: http://127.0.0.1:8000/subjects/pedagogy/")
        print(f"   • Voir les programmes dans l'admin: http://127.0.0.1:8000/admin/")
        print(f"   • Consulter l'onglet pédagogique de la classe: http://127.0.0.1:8000/classes/classes/{school_class.id}/")
        print(f"   • Générer automatiquement l'emploi du temps dans l'onglet 'Emploi du temps'")
        
    except SchoolClass.DoesNotExist:
        print("❌ Classe '6e M1' non trouvée. Créez d'abord cette classe.")
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        import traceback
        traceback.print_exc()

def cleanup_sample_data():
    """Supprime les données d'exemple créées"""
    print("🧹 Nettoyage des données d'exemple...")
    
    try:
        # Supprimer les programmes créés par notre script
        programs_to_delete = SubjectProgram.objects.filter(
            created_by__isnull=False
        )
        count = programs_to_delete.count()
        programs_to_delete.delete()
        print(f"✅ {count} programmes supprimés")
        
        print("✅ Nettoyage terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        cleanup_sample_data()
    else:
        create_sample_data()
