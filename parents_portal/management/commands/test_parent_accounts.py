from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from students.models import Student, Guardian
from parents_portal.models import ParentUser, ParentStudentRelation
from parents_portal.services import ParentPortalService

class Command(BaseCommand):
    """
    Commande pour tester la création des comptes parents
    """
    help = 'Teste la création automatique des comptes parents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Exécute en mode test sans créer réellement les comptes',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Limite le nombre de comptes à tester (défaut: 5)',
        )

    def handle(self, *args, **options):
        """Exécute la commande de test"""
        try:
            dry_run = options['dry_run']
            limit = options['limit']
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🧪 Test de création des comptes parents"
                    f"{' (mode dry-run)' if dry_run else ''}\n"
                )
            )
            
            # Vérifier les guardians disponibles
            guardians_with_email = Guardian.objects.filter(
                email__isnull=False
            ).exclude(email='')[:limit]
            
            if not guardians_with_email:
                self.stdout.write(
                    self.style.WARNING(
                        "❌ Aucun guardian avec email trouvé. "
                        "Vous devez d'abord créer des étudiants avec des guardians ayant des emails."
                    )
                )
                return
            
            self.stdout.write(f"📧 {guardians_with_email.count()} guardian(s) avec email trouvé(s)")
            
            # Statistiques
            created_count = 0
            error_count = 0
            already_exists_count = 0
            
            for guardian in guardians_with_email:
                try:
                    self.stdout.write(f"\n👨‍👩‍👧‍👦 Test pour {guardian.name} ({guardian.email})")
                    self.stdout.write(f"   • Relation: {guardian.relation}")
                    self.stdout.write(f"   • Étudiant: {guardian.student}")
                    
                    # Vérifier si le compte existe déjà
                    if ParentUser.objects.filter(email=guardian.email).exists():
                        self.stdout.write(
                            self.style.WARNING(f"   ⚠️  Compte déjà existant pour {guardian.email}")
                        )
                        already_exists_count += 1
                        continue
                    
                    if not dry_run:
                        # Créer le compte
                        parent_user = ParentPortalService.create_parent_account(guardian)
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"   ✅ Compte créé avec succès!"
                            )
                        )
                        self.stdout.write(f"      • Username: {parent_user.username}")
                        self.stdout.write(f"      • Email: {parent_user.email}")
                        self.stdout.write(f"      • Rôle: {parent_user.role}")
                        
                        # Vérifier les relations
                        relations = ParentStudentRelation.objects.filter(parent_user=parent_user)
                        self.stdout.write(f"      • Relations créées: {relations.count()}")
                        
                        created_count += 1
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f"   ✅ [DRY-RUN] Compte serait créé")
                        )
                        self.stdout.write(f"      • Email: {guardian.email}")
                        self.stdout.write(f"      • Relation: {guardian.relation}")
                        created_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Erreur: {str(e)}")
                    )
                    error_count += 1
            
            # Résumé
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.SUCCESS("📊 RÉSUMÉ DES TESTS"))
            self.stdout.write("="*50)
            self.stdout.write(f"✅ Comptes créés avec succès: {created_count}")
            self.stdout.write(f"⚠️  Comptes déjà existants: {already_exists_count}")
            self.stdout.write(f"❌ Erreurs rencontrées: {error_count}")
            
            if not dry_run and created_count > 0:
                self.stdout.write("\n" + self.style.SUCCESS("🎉 Test terminé avec succès!"))
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️  N'oubliez pas de configurer les paramètres email pour l'envoi des identifiants."
                    )
                )
            elif dry_run:
                self.stdout.write("\n" + self.style.SUCCESS("🧪 Test en mode dry-run terminé!"))
                self.stdout.write("Pour créer réellement les comptes, relancez sans --dry-run")
                
        except Exception as e:
            raise CommandError(f"Erreur lors du test: {str(e)}")
