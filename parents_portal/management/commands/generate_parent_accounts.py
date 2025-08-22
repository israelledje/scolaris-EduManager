from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

from students.models import Guardian
from parents_portal.models import ParentUser, ParentStudentRelation
from parents_portal.services import ParentPortalService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Commande pour générer les comptes parents pour tous les guardians existants
    """
    help = 'Génère automatiquement les comptes parents pour tous les guardians existants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule la création sans créer réellement les comptes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la création même si des comptes existent déjà',
        )
        parser.add_argument(
            '--email-only',
            action='store_true',
            help='Génère seulement les comptes pour les guardians avec email',
        )
        parser.add_argument(
            '--guardian-id',
            type=int,
            help='Génère le compte pour un guardian spécifique (ID)',
        )
        parser.add_argument(
            '--resend-credentials',
            action='store_true',
            help='Renvoie les identifiants aux parents existants',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Démarrage de la génération des comptes parents...')
        )

        try:
            if options['guardian_id']:
                # Générer le compte pour un guardian spécifique
                self._generate_single_guardian_account(options['guardian_id'], options)
            elif options['resend_credentials']:
                # Renvoyer les identifiants aux parents existants
                self._resend_credentials_to_existing_parents(options)
            else:
                # Générer les comptes pour tous les guardians
                self._generate_all_guardian_accounts(options)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la génération : {str(e)}')
            )
            raise CommandError(str(e))

    def _generate_single_guardian_account(self, guardian_id, options):
        """Génère le compte pour un guardian spécifique"""
        try:
            guardian = Guardian.objects.get(id=guardian_id)
            self.stdout.write(f'📧 Génération du compte pour {guardian.name} ({guardian.email})')
            
            if not guardian.email:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Guardian {guardian.name} n\'a pas d\'email')
                )
                return

            if ParentUser.objects.filter(email=guardian.email).exists() and not options['force']:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Compte déjà existant pour {guardian.email}')
                )
                return

            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ [DRY RUN] Compte serait créé pour {guardian.email}')
                )
                return

            # Créer le compte
            parent_user = ParentPortalService.create_parent_account(guardian)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Compte créé avec succès pour {guardian.email}')
            )

        except Guardian.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Guardian avec ID {guardian_id} non trouvé')
            )

    def _generate_all_guardian_accounts(self, options):
        """Génère les comptes pour tous les guardians"""
        # Récupérer tous les guardians
        guardians = Guardian.objects.all()
        
        if options['email_only']:
            guardians = guardians.filter(email__isnull=False).exclude(email='')
            self.stdout.write(f'📧 Génération des comptes pour {guardians.count()} guardians avec email')
        else:
            self.stdout.write(f'👥 Génération des comptes pour {guardians.count()} guardians')

        # Statistiques
        total_guardians = guardians.count()
        accounts_created = 0
        accounts_existing = 0
        accounts_failed = 0
        emails_sent = 0
        emails_failed = 0

        for guardian in guardians:
            try:
                # Vérifier si le guardian a un email
                if not guardian.email:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Guardian {guardian.name} ignoré (pas d\'email)')
                    )
                    continue

                # Vérifier si un compte existe déjà
                if ParentUser.objects.filter(email=guardian.email).exists():
                    if options['force']:
                        self.stdout.write(
                            self.style.WARNING(f'🔄 Compte existant pour {guardian.email} - régénération forcée')
                        )
                        # Supprimer l'ancien compte
                        ParentUser.objects.filter(email=guardian.email).delete()
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Compte déjà existant pour {guardian.email}')
                        )
                        accounts_existing += 1
                        continue

                if options['dry_run']:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ [DRY RUN] Compte serait créé pour {guardian.email}')
                    )
                    accounts_created += 1
                    continue

                # Créer le compte
                with transaction.atomic():
                    parent_user = ParentPortalService.create_parent_account(guardian)
                    accounts_created += 1
                    emails_sent += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Compte créé pour {guardian.email}')
                    )

            except Exception as e:
                accounts_failed += 1
                emails_failed += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur pour {guardian.email}: {str(e)}')
                )
                logger.error(f"Erreur création compte pour {guardian.email}: {str(e)}")

        # Affichage des statistiques
        self._display_statistics(
            total_guardians, accounts_created, accounts_existing, 
            accounts_failed, emails_sent, emails_failed, options
        )

    def _resend_credentials_to_existing_parents(self, options):
        """Renvoie les identifiants aux parents existants"""
        self.stdout.write('📧 Renvoi des identifiants aux parents existants...')
        
        parents = ParentUser.objects.filter(is_active=True)
        total_parents = parents.count()
        emails_sent = 0
        emails_failed = 0

        for parent in parents:
            try:
                if not parent.email:
                    continue

                # Générer un nouveau mot de passe temporaire
                new_password = parent.generate_temporary_password()
                parent.set_password(new_password)
                parent.save()

                # Envoyer l'email
                if parent.send_credentials_email(new_password):
                    emails_sent += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Identifiants renvoyés à {parent.email}')
                    )
                else:
                    emails_failed += 1
                    self.stdout.write(
                        self.style.ERROR(f'❌ Échec envoi à {parent.email}')
                    )

            except Exception as e:
                emails_failed += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur pour {parent.email}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'📊 Résumé: {emails_sent}/{total_parents} emails envoyés, '
                f'{emails_failed} échecs'
            )
        )

    def _display_statistics(self, total, created, existing, failed, emails_sent, emails_failed, options):
        """Affiche les statistiques de la génération"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 STATISTIQUES DE GÉNÉRATION'))
        self.stdout.write('='*60)
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 MODE SIMULATION (DRY RUN)'))
        
        self.stdout.write(f'👥 Total des guardians: {total}')
        self.stdout.write(f'✅ Comptes créés: {created}')
        self.stdout.write(f'⚠️  Comptes existants: {existing}')
        self.stdout.write(f'❌ Échecs: {failed}')
        self.stdout.write(f'📧 Emails envoyés: {emails_sent}')
        self.stdout.write(f'📧 Échecs email: {emails_failed}')
        
        if created > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 {created} comptes parents ont été créés avec succès !')
            )
        
        if failed > 0:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  {failed} comptes n\'ont pas pu être créés')
            )

        self.stdout.write('='*60 + '\n')

    def _validate_environment(self):
        """Valide que l'environnement est correctement configuré"""
        # Vérifier la configuration email
        if not hasattr(settings, 'EMAIL_HOST') or settings.EMAIL_HOST == 'EMAIL_HOST':
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Configuration email non définie. '
                    'Les emails ne pourront pas être envoyés.'
                )
            )
            return False
        
        # Vérifier que l'application est dans INSTALLED_APPS
        if 'parents_portal' not in settings.INSTALLED_APPS:
            self.stdout.write(
                self.style.ERROR(
                    '❌ L\'application parents_portal n\'est pas dans INSTALLED_APPS'
                )
            )
            return False
        
        return True
