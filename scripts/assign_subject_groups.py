#!/usr/bin/env python3
"""
Script pour attribuer des groupes aux matières existantes dans la base de données.

Ce script analyse les matières existantes et leur attribue automatiquement
un groupe (Groupe 1 ou Groupe 2) basé sur des règles prédéfinies.

Usage:
    python manage.py shell < scripts/assign_subject_groups.py
    ou
    python scripts/assign_subject_groups.py
"""

import os
import sys
import django

# Configuration Django
if __name__ == "__main__":
    # Ajouter le répertoire parent au path pour importer le projet Django
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
    django.setup()

from subjects.models import Subject

def assign_subject_groups():
    """
    Attribue des groupes aux matières existantes basé sur des règles prédéfinies.
    """
    
    # Définition des groupes de matières selon le système éducatif camerounais
    GROUP_1_SUBJECTS = {
        # Matières principales (fondamentales) - Groupe 1
        'français', 'francais', 'langue française',
        'anglais', 'langue anglaise', 'english',
        'mathématiques', 'maths', 'math', 'mathematiques',
        'sciences de la vie et de la terre', 'svt', 'biologie',
        'physique', 'physique-chimie', 'sciences physiques', 'chimie',
        'pct', 'physique-chimie-technologie',
        'histoire', 'histoire-géographie', 'histoire-geographie',
        'géographie', 'geographie',
        'philosophie', 'philo',
        
        # Matières littéraires principales
        'littérature', 'litterature', 'français-littérature',
        'sciences économiques et sociales', 'ses',
        'économie', 'economie',
        'sociologie', 'psychologie',
        
        # Langues principales
        'espagnol', 'langue espagnole', 'spanish',
        'allemand', 'langue allemande', 'german',
        'italien', 'langue italienne', 'italian',
        'portugais', 'langue portugaise', 'portuguese',
        'arabe', 'langue arabe', 'arabic',
        'chinois', 'langue chinoise', 'chinese',
        
        # Langues anciennes
        'latin', 'grec', 'grec ancien', 'langues anciennes',
    }
    
    GROUP_2_SUBJECTS = {
        # Matières complémentaires (d'accompagnement) - Groupe 2
        'éducation physique et sportive', 'eps', 'sport',
        'éducation physique', 'education physique',
        'éducation à la citoyenneté et à la morale', 'ecm',
        'éducation civique', 'education civique', 'civisme',
        'arts plastiques', 'arts-plastiques', 'arts', 'dessin',
        'musique', 'éducation musicale', 'education musicale',
        'technologie', 'techno',
        'informatique', 'informatique générale',
        
        # Matières artistiques et culturelles
        'théâtre', 'theatre', 'art dramatique',
        'cinéma', 'cinema', 'audiovisuel',
        'histoire des arts', 'histoire de l\'art',
        'design', 'graphisme', 'communication visuelle',
        'mode', 'stylisme', 'création textile',
        'céramique', 'ceramique', 'poterie',
        'sculpture', 'peinture', 'gravure',
        
        # Matières techniques spécialisées
        'algorithmique', 'programmation', 'génie logiciel',
        'architecture des ordinateurs', 'structures de données',
        'systèmes d\'exploitation', 'travail manuel', 'tm',
        'bases de données', 'réseaux informatiques',
        'sécurité informatique', 'développement web',
        'développement mobile', 'intelligence artificielle',
        'machine learning', 'data science', 'big data',
        
        # Matières professionnelles et techniques spécialisées
        'comptabilité', 'comptabilite', 'gestion',
        'marketing', 'vente', 'commerce',
        'secrétariat', 'secretariat', 'bureautique',
        'informatique de gestion', 'informatique bureautique',
        'maintenance', 'mécanique', 'mecanique',
        'électricité', 'electricite', 'électronique', 'electronique',
        'plomberie', 'maçonnerie', 'maconnerie',
        'menuiserie', 'ébénisterie', 'ebenisterie',
        'cuisine', 'restauration', 'hôtellerie', 'hotellerie',
        'tourisme', 'accueil', 'service',
        'coiffure', 'esthétique', 'esthetique',
        'santé', 'sante', 'soins infirmiers',
        'agriculture', 'agronomie', 'élevage', 'elevage',
        'vétérinaire', 'veterinaire', 'sciences vétérinaires',
        
        # Matières de formation professionnelle
        'formation professionnelle', 'stage', 'alternance',
        'apprentissage', 'formation en entreprise',
        'projet professionnel', 'orientation',
        'vie professionnelle', 'droit du travail',
        
        # Matières spécialisées
        'religion', 'catéchèse', 'catechese',
        'morale', 'éthique', 'ethique',
        'développement personnel', 'developpement personnel',
        'méditation', 'yoga', 'relaxation',
    }
    
    print("🔍 Analyse des matières existantes...")
    
    # Récupérer toutes les matières
    subjects = Subject.objects.all()
    total_subjects = subjects.count()
    
    if total_subjects == 0:
        print("❌ Aucune matière trouvée dans la base de données.")
        return
    
    print(f"📚 {total_subjects} matière(s) trouvée(s)")
    
    # Statistiques
    group_1_count = 0
    group_2_count = 0
    unchanged_count = 0
    updated_subjects = []
    
    for subject in subjects:
        subject_name_lower = subject.name.lower().strip()
        assigned_group = None
        
        # Vérifier si la matière appartient au Groupe 1
        if any(keyword in subject_name_lower for keyword in GROUP_1_SUBJECTS):
            assigned_group = 1
        # Vérifier si la matière appartient au Groupe 2
        elif any(keyword in subject_name_lower for keyword in GROUP_2_SUBJECTS):
            assigned_group = 2
        
        # Si un groupe a été déterminé et qu'il est différent du groupe actuel
        if assigned_group and subject.group != assigned_group:
            old_group = subject.get_group_display()
            subject.group = assigned_group
            subject.save()
            
            new_group = subject.get_group_display()
            updated_subjects.append({
                'name': subject.name,
                'old_group': old_group,
                'new_group': new_group
            })
            
            if assigned_group == 1:
                group_1_count += 1
            else:
                group_2_count += 1
                
            print(f"✅ {subject.name}: {old_group} → {new_group}")
        else:
            unchanged_count += 1
            if assigned_group:
                print(f"ℹ️  {subject.name}: déjà dans le {subject.get_group_display()}")
            else:
                print(f"⚠️  {subject.name}: groupe non déterminé automatiquement")
    
    # Affichage du résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE L'ATTRIBUTION DES GROUPES")
    print("="*60)
    print(f"📚 Total des matières: {total_subjects}")
    print(f"✅ Matières mises à jour: {len(updated_subjects)}")
    print(f"   - Attribuées au Groupe 1: {group_1_count}")
    print(f"   - Attribuées au Groupe 2: {group_2_count}")
    print(f"ℹ️  Matières inchangées: {unchanged_count}")
    
    if updated_subjects:
        print(f"\n📝 DÉTAIL DES MODIFICATIONS:")
        for subject_info in updated_subjects:
            print(f"   • {subject_info['name']}: {subject_info['old_group']} → {subject_info['new_group']}")
    
    # Vérification finale
    print(f"\n🔍 VÉRIFICATION FINALE:")
    final_group_1 = Subject.objects.filter(group=1).count()
    final_group_2 = Subject.objects.filter(group=2).count()
    print(f"   - Matières dans le Groupe 1: {final_group_1}")
    print(f"   - Matières dans le Groupe 2: {final_group_2}")
    
    print(f"\n✨ Attribution des groupes terminée avec succès!")

def show_subject_groups():
    """
    Affiche la répartition actuelle des matières par groupe.
    """
    print("📊 RÉPARTITION ACTUELLE DES MATIÈRES PAR GROUPE")
    print("="*60)
    
    group_1_subjects = Subject.objects.filter(group=1).order_by('name')
    group_2_subjects = Subject.objects.filter(group=2).order_by('name')
    
    print(f"\n📚 GROUPE 1 ({group_1_subjects.count()} matière(s)):")
    for subject in group_1_subjects:
        print(f"   • {subject.name}")
    
    print(f"\n📚 GROUPE 2 ({group_2_subjects.count()} matière(s)):")
    for subject in group_2_subjects:
        print(f"   • {subject.name}")

if __name__ == "__main__":
    print("🚀 Script d'attribution des groupes de matières")
    print("="*60)
    
    # Afficher l'état actuel
    show_subject_groups()
    
    print(f"\n{'='*60}")
    response = input("Voulez-vous procéder à l'attribution automatique des groupes? (o/N): ")
    
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        assign_subject_groups()
    else:
        print("❌ Opération annulée.")
