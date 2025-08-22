from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from students.models import Guardian
from parents_portal.models import ParentUser, ParentStudentRelation

class Command(BaseCommand):
    """
    Commande pour vérifier l'état des comptes parents
    """
    help = 'Vérifie l\'état des comptes parents et des relations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Affiche des détails sur chaque compte',
        )
        parser.add_argument(
            '--orphaned',
            action='store_true',
            help='Affiche seulement les comptes orphelins (sans étudiants)',
        )
        parser.add_argument(
            '--inactive',
            action='store_true',
            help='Affiche seulement les comptes inactifs',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Vérification de l\'état des comptes parents...')
        )

        try:
            self._check_overall_status()
            
            if options['detailed']:
                self._show_detailed_status()
            
            if options['orphaned']:
                self._show_orphaned_accounts()
            
            if options['inactive']:
                self._show_inactive_accounts()
            
            self._show_recommendations()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la vérification : {str(e)}')
            )

    def _check_overall_status(self):
        """Vérifie le statut général des comptes"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 STATUT GÉNÉRAL DES COMPTES'))
        self.stdout.write('='*60)

        # Statistiques des guardians
        total_guardians = Guardian.objects.count()
        guardians_with_email = Guardian.objects.filter(email__isnull=False).exclude(email='').count()
        guardians_without_email = total_guardians - guardians_with_email

        self.stdout.write(f'👥 Total des guardians: {total_guardians}')
        self.stdout.write(f'📧 Guardians avec email: {guardians_with_email}')
        self.stdout.write(f'⚠️  Guardians sans email: {guardians_without_email}')

        # Statistiques des comptes parents
        total_parents = ParentUser.objects.count()
        active_parents = ParentUser.objects.filter(is_active=True).count()
        inactive_parents = total_parents - active_parents
        verified_parents = ParentUser.objects.filter(is_verified=True).count()
        unverified_parents = total_parents - verified_parents

        self.stdout.write(f'\n👨‍👩‍👧‍👦 Total des comptes parents: {total_parents}')
        self.stdout.write(f'✅ Comptes actifs: {active_parents}')
        self.stdout.write(f'❌ Comptes inactifs: {inactive_parents}')
        self.stdout.write(f'🔐 Comptes vérifiés: {verified_parents}')
        self.stdout.write(f'⏳ Comptes non vérifiés: {unverified_parents}')

        # Statistiques des relations
        total_relations = ParentStudentRelation.objects.count()
        active_relations = ParentStudentRelation.objects.filter(
            parent__is_active=True
        ).count()

        self.stdout.write(f'\n🔗 Total des relations: {total_relations}')
        self.stdout.write(f'✅ Relations actives: {active_relations}')

        # Calcul des pourcentages
        if total_guardians > 0:
            coverage_percentage = (total_parents / total_guardians) * 100
            self.stdout.write(f'\n📈 Couverture: {coverage_percentage:.1f}% des guardians ont un compte')

        if total_parents > 0:
            active_percentage = (active_parents / total_parents) * 100
            verified_percentage = (verified_parents / total_parents) * 100
            self.stdout.write(f'📊 {active_percentage:.1f}% des comptes sont actifs')
            self.stdout.write(f'🔐 {verified_percentage:.1f}% des comptes sont vérifiés')

    def _show_detailed_status(self):
        """Affiche le statut détaillé de chaque compte"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📋 STATUT DÉTAILLÉ DES COMPTES'))
        self.stdout.write('='*60)

        parents = ParentUser.objects.all().order_by('created_at')
        
        for parent in parents:
            # Compter les étudiants
            student_count = parent.students.count()
            
            # Dernière connexion
            last_login = parent.last_login.strftime('%d/%m/%Y %H:%M') if parent.last_login else 'Jamais'
            
            # Statut du compte
            status = '✅ Actif' if parent.is_active else '❌ Inactif'
            verified = '🔐 Vérifié' if parent.is_verified else '⏳ Non vérifié'
            
            self.stdout.write(
                f'\n👤 {parent.get_full_name()} ({parent.email})'
            )
            self.stdout.write(f'   ID: {parent.parent_id} | {status} | {verified}')
            self.stdout.write(f'   Étudiants: {student_count} | Dernière connexion: {last_login}')
            self.stdout.write(f'   Créé le: {parent.created_at.strftime("%d/%m/%Y")}')

    def _show_orphaned_accounts(self):
        """Affiche les comptes orphelins (sans étudiants)"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.WARNING('🚨 COMPTES ORPHELINS (SANS ÉTUDIANTS)'))
        self.stdout.write('='*60)

        orphaned_parents = ParentUser.objects.annotate(
            student_count=Count('students')
        ).filter(student_count=0)

        if orphaned_parents.exists():
            for parent in orphaned_parents:
                self.stdout.write(
                    f'👤 {parent.get_full_name()} ({parent.email}) - '
                    f'Créé le {parent.created_at.strftime("%d/%m/%Y")}'
                )
        else:
            self.stdout.write(self.style.SUCCESS('✅ Aucun compte orphelin trouvé'))

    def _show_inactive_accounts(self):
        """Affiche les comptes inactifs"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.WARNING('⏸️  COMPTES INACTIFS'))
        self.stdout.write('='*60)

        inactive_parents = ParentUser.objects.filter(is_active=False)

        if inactive_parents.exists():
            for parent in inactive_parents:
                student_count = parent.students.count()
                self.stdout.write(
                    f'👤 {parent.get_full_name()} ({parent.email}) - '
                    f'{student_count} étudiant(s) - '
                    f'Désactivé le {parent.updated_at.strftime("%d/%m/%Y")}'
                )
        else:
            self.stdout.write(self.style.SUCCESS('✅ Aucun compte inactif trouvé'))

    def _show_recommendations(self):
        """Affiche des recommandations basées sur l'état des comptes"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('💡 RECOMMANDATIONS'))
        self.stdout.write('='*60)

        # Vérifier les guardians sans email
        guardians_without_email = Guardian.objects.filter(
            Q(email__isnull=True) | Q(email='')
        ).count()
        
        if guardians_without_email > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  {guardians_without_email} guardians n\'ont pas d\'email. '
                    'Ajoutez des emails pour permettre la création de comptes.'
                )
            )

        # Vérifier les comptes non vérifiés
        unverified_parents = ParentUser.objects.filter(is_verified=False).count()
        if unverified_parents > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⏳ {unverified_parents} comptes ne sont pas vérifiés. '
                    'Envisagez d\'envoyer des emails de vérification.'
                )
            )

        # Vérifier les comptes orphelins
        orphaned_count = ParentUser.objects.annotate(
            student_count=Count('students')
        ).filter(student_count=0).count()
        
        if orphaned_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'🚨 {orphaned_count} comptes n\'ont pas d\'étudiants associés. '
                    'Vérifiez les relations ou supprimez ces comptes.'
                )
            )

        # Vérifier les comptes inactifs
        inactive_count = ParentUser.objects.filter(is_active=False).count()
        if inactive_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⏸️  {inactive_count} comptes sont inactifs. '
                    'Réactivez-les si nécessaire ou supprimez-les.'
                )
            )

        # Recommandations générales
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Recommandations générales:'
            )
        )
        self.stdout.write('   • Exécutez régulièrement cette commande pour surveiller l\'état')
        self.stdout.write('   • Utilisez --detailed pour un aperçu complet')
        self.stdout.write('   • Gérez les comptes orphelins et inactifs')
        self.stdout.write('   • Vérifiez la configuration email pour les nouveaux comptes')

        self.stdout.write('='*60 + '\n')
