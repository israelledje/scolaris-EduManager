from django.core.management.base import BaseCommand
from subjects.models import Subject

class Command(BaseCommand):
    help = 'Attribue automatiquement des groupes aux matières existantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les modifications qui seraient effectuées sans les appliquer',
        )
        parser.add_argument(
            '--show-only',
            action='store_true',
            help='Affiche seulement la répartition actuelle des matières',
        )

    def handle(self, *args, **options):
        if options['show_only']:
            self.show_subject_groups()
            return

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('Mode simulation activé - aucune modification ne sera effectuée')
            )
            self.assign_subject_groups(dry_run=True)
        else:
            self.assign_subject_groups(dry_run=False)

    def show_subject_groups(self):
        """Affiche la répartition actuelle des matières par groupe."""
        self.stdout.write(
            self.style.SUCCESS('📊 RÉPARTITION ACTUELLE DES MATIÈRES PAR GROUPE')
        )
        self.stdout.write('='*60)
        
        group_1_subjects = Subject.objects.filter(group=1).order_by('name')
        group_2_subjects = Subject.objects.filter(group=2).order_by('name')
        
        self.stdout.write(f'\n📚 GROUPE 1 ({group_1_subjects.count()} matière(s)):')
        for subject in group_1_subjects:
            self.stdout.write(f'   • {subject.name}')
        
        self.stdout.write(f'\n📚 GROUPE 2 ({group_2_subjects.count()} matière(s)):')
        for subject in group_2_subjects:
            self.stdout.write(f'   • {subject.name}')

    def assign_subject_groups(self, dry_run=False):
        """Attribue des groupes aux matières existantes."""
        
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
        
        self.stdout.write('🔍 Analyse des matières existantes...')
        
        # Récupérer toutes les matières
        subjects = Subject.objects.all()
        total_subjects = subjects.count()
        
        if total_subjects == 0:
            self.stdout.write(
                self.style.ERROR('❌ Aucune matière trouvée dans la base de données.')
            )
            return
        
        self.stdout.write(f'📚 {total_subjects} matière(s) trouvée(s)')
        
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
                new_group = 'Groupe 1' if assigned_group == 1 else 'Groupe 2'
                
                updated_subjects.append({
                    'name': subject.name,
                    'old_group': old_group,
                    'new_group': new_group
                })
                
                if assigned_group == 1:
                    group_1_count += 1
                else:
                    group_2_count += 1
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f'🔄 {subject.name}: {old_group} → {new_group} (simulation)')
                    )
                else:
                    subject.group = assigned_group
                    subject.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {subject.name}: {old_group} → {new_group}')
                    )
            else:
                unchanged_count += 1
                if assigned_group:
                    self.stdout.write(f'ℹ️  {subject.name}: déjà dans le {subject.get_group_display()}')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {subject.name}: groupe non déterminé automatiquement')
                    )
        
        # Affichage du résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📊 RÉSUMÉ DE L\'ATTRIBUTION DES GROUPES')
        self.stdout.write('='*60)
        self.stdout.write(f'📚 Total des matières: {total_subjects}')
        
        if dry_run:
            self.stdout.write(f'🔄 Modifications qui seraient effectuées: {len(updated_subjects)}')
        else:
            self.stdout.write(f'✅ Matières mises à jour: {len(updated_subjects)}')
        
        self.stdout.write(f'   - Attribuées au Groupe 1: {group_1_count}')
        self.stdout.write(f'   - Attribuées au Groupe 2: {group_2_count}')
        self.stdout.write(f'ℹ️  Matières inchangées: {unchanged_count}')
        
        if updated_subjects:
            self.stdout.write(f'\n📝 DÉTAIL DES MODIFICATIONS:')
            for subject_info in updated_subjects:
                self.stdout.write(f'   • {subject_info["name"]}: {subject_info["old_group"]} → {subject_info["new_group"]}')
        
        # Vérification finale
        self.stdout.write(f'\n🔍 VÉRIFICATION FINALE:')
        final_group_1 = Subject.objects.filter(group=1).count()
        final_group_2 = Subject.objects.filter(group=2).count()
        self.stdout.write(f'   - Matières dans le Groupe 1: {final_group_1}')
        self.stdout.write(f'   - Matières dans le Groupe 2: {final_group_2}')
        
        if dry_run:
            self.stdout.write(f'\n✨ Simulation terminée! Utilisez sans --dry-run pour appliquer les modifications.')
        else:
            self.stdout.write(f'\n✨ Attribution des groupes terminée avec succès!')
