"""
Utilitaires pour la gestion des comptes parents
"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import ParentUser, ParentStudentRelation
from students.models import Guardian

logger = logging.getLogger(__name__)

class ParentAccountManager:
    """Gestionnaire des comptes parents avec utilitaires"""
    
    @staticmethod
    def bulk_create_parent_accounts(guardians=None, force=False, dry_run=False):
        """
        Crée en masse les comptes parents pour les guardians
        
        Args:
            guardians: Liste des guardians (si None, prend tous les guardians avec email)
            force: Force la création même si des comptes existent
            dry_run: Mode simulation sans création réelle
            
        Returns:
            dict: Statistiques de la création
        """
        if guardians is None:
            guardians = Guardian.objects.filter(email__isnull=False).exclude(email='')
        
        stats = {
            'total': guardians.count(),
            'created': 0,
            'existing': 0,
            'failed': 0,
            'emails_sent': 0,
            'emails_failed': 0,
            'errors': []
        }
        
        for guardian in guardians:
            try:
                if not guardian.email:
                    continue
                
                # Vérifier si un compte existe déjà
                if ParentUser.objects.filter(email=guardian.email).exists():
                    if force:
                        # Supprimer l'ancien compte
                        ParentUser.objects.filter(email=guardian.email).delete()
                        logger.info(f"Compte existant supprimé pour {guardian.email}")
                    else:
                        stats['existing'] += 1
                        continue
                
                if dry_run:
                    stats['created'] += 1
                    continue
                
                # Créer le compte
                with transaction.atomic():
                    from .services import ParentPortalService
                    parent_user = ParentPortalService.create_parent_account(guardian)
                    stats['created'] += 1
                    stats['emails_sent'] += 1
                    
                    logger.info(f"Compte créé avec succès pour {guardian.email}")
                    
            except Exception as e:
                stats['failed'] += 1
                stats['emails_failed'] += 1
                error_msg = f"Erreur pour {guardian.email}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        return stats
    
    @staticmethod
    def resend_credentials_to_parents(parents=None, force_new_password=False):
        """
        Renvoie les identifiants aux parents existants
        
        Args:
            parents: Liste des parents (si None, prend tous les parents actifs)
            force_new_password: Force la génération d'un nouveau mot de passe
            
        Returns:
            dict: Statistiques de l'envoi
        """
        if parents is None:
            parents = ParentUser.objects.filter(is_active=True)
        
        stats = {
            'total': parents.count(),
            'emails_sent': 0,
            'emails_failed': 0,
            'errors': []
        }
        
        for parent in parents:
            try:
                if not parent.email:
                    continue
                
                # Générer un nouveau mot de passe si demandé
                if force_new_password:
                    new_password = parent.generate_temporary_password()
                    parent.set_password(new_password)
                    parent.save()
                else:
                    # Utiliser le mot de passe existant (non recommandé en production)
                    new_password = "Mot de passe existant"
                
                # Envoyer l'email
                if parent.send_credentials_email(new_password):
                    stats['emails_sent'] += 1
                    logger.info(f"Identifiants renvoyés à {parent.email}")
                else:
                    stats['emails_failed'] += 1
                    error_msg = f"Échec envoi à {parent.email}"
                    stats['errors'].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                stats['emails_failed'] += 1
                error_msg = f"Erreur pour {parent.email}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        return stats
    
    @staticmethod
    def cleanup_orphaned_accounts():
        """
        Nettoie les comptes orphelins (sans étudiants)
        
        Returns:
            dict: Statistiques du nettoyage
        """
        stats = {
            'total_orphaned': 0,
            'deactivated': 0,
            'deleted': 0,
            'errors': []
        }
        
        # Trouver les comptes orphelins
        orphaned_parents = ParentUser.objects.annotate(
            student_count=ParentUser.students.through.objects.filter(
                parentuser_id=models.OuterRef('pk')
            ).values('parentuser_id').annotate(
                count=models.Count('student_id')
            ).values('count')
        ).filter(student_count=0)
        
        stats['total_orphaned'] = orphaned_parents.count()
        
        for parent in orphaned_parents:
            try:
                # Désactiver le compte
                parent.is_active = False
                parent.save()
                stats['deactivated'] += 1
                
                logger.info(f"Compte orphelin désactivé: {parent.email}")
                
            except Exception as e:
                error_msg = f"Erreur désactivation {parent.email}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        return stats
    
    @staticmethod
    def validate_parent_accounts():
        """
        Valide l'intégrité des comptes parents
        
        Returns:
            dict: Résultats de la validation
        """
        results = {
            'valid': 0,
            'invalid': 0,
            'warnings': 0,
            'issues': []
        }
        
        parents = ParentUser.objects.all()
        
        for parent in parents:
            issues = []
            
            # Vérifier l'email
            if not parent.email:
                issues.append("Email manquant")
            
            # Vérifier les relations avec les étudiants
            student_count = parent.students.count()
            if student_count == 0:
                issues.append("Aucun étudiant associé")
            
            # Vérifier la cohérence des données
            if not parent.first_name or not parent.last_name:
                issues.append("Nom/prénom manquant")
            
            # Vérifier le statut
            if not parent.is_active:
                issues.append("Compte inactif")
            
            if issues:
                results['invalid'] += 1
                results['issues'].append({
                    'parent': parent,
                    'issues': issues
                })
            else:
                results['valid'] += 1
        
        return results
    
    @staticmethod
    def get_parent_statistics():
        """
        Récupère des statistiques détaillées sur les comptes parents
        
        Returns:
            dict: Statistiques détaillées
        """
        from django.db.models import Count, Q
        
        # Statistiques de base
        total_parents = ParentUser.objects.count()
        active_parents = ParentUser.objects.filter(is_active=True).count()
        verified_parents = ParentUser.objects.filter(is_verified=True).count()
        
        # Statistiques des relations
        total_relations = ParentStudentRelation.objects.count()
        active_relations = ParentStudentRelation.objects.filter(
            parent__is_active=True
        ).count()
        
        # Statistiques des guardians
        total_guardians = Guardian.objects.count()
        guardians_with_email = Guardian.objects.filter(
            email__isnull=False
        ).exclude(email='').count()
        
        # Statistiques de connexion
        recent_logins = ParentUser.objects.filter(
            last_login__gte=timezone.now() - timezone.timedelta(days=30)
        ).count()
        
        # Statistiques des rôles
        role_stats = ParentUser.objects.values('role').annotate(
            count=Count('id')
        ).order_by('role')
        
        # Statistiques des étudiants par parent
        student_distribution = ParentUser.objects.annotate(
            student_count=Count('students')
        ).values('student_count').annotate(
            parent_count=Count('id')
        ).order_by('student_count')
        
        return {
            'total_parents': total_parents,
            'active_parents': active_parents,
            'verified_parents': verified_parents,
            'total_relations': total_relations,
            'active_relations': active_relations,
            'total_guardians': total_guardians,
            'guardians_with_email': guardians_with_email,
            'recent_logins': recent_logins,
            'role_stats': list(role_stats),
            'student_distribution': list(student_distribution),
            'coverage_percentage': (total_parents / total_guardians * 100) if total_guardians > 0 else 0,
            'active_percentage': (active_parents / total_parents * 100) if total_parents > 0 else 0,
            'verified_percentage': (verified_parents / total_parents * 100) if total_parents > 0 else 0,
        }

def send_parent_notification_email(parent, subject, message, template=None):
    """
    Envoie un email de notification à un parent
    
    Args:
        parent: Instance ParentUser
        subject: Sujet de l'email
        message: Message de l'email
        template: Template HTML optionnel
        
    Returns:
        bool: True si l'email a été envoyé avec succès
    """
    try:
        if not parent.email:
            logger.warning(f"Parent {parent.id} n'a pas d'email")
            return False
        
        # Envoyer l'email
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@scolaris.com'),
            recipient_list=[parent.email],
            fail_silently=False,
        )
        
        logger.info(f"Email de notification envoyé à {parent.email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur envoi email à {parent.email}: {str(e)}")
        return False

def export_parent_accounts_to_csv(file_path):
    """
    Exporte les comptes parents vers un fichier CSV
    
    Args:
        file_path: Chemin du fichier CSV à créer
        
    Returns:
        bool: True si l'export a réussi
    """
    import csv
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'ID', 'Parent ID', 'Nom', 'Prénom', 'Email', 'Téléphone', 
                'Rôle', 'Statut', 'Vérifié', 'Étudiants', 'Dernière connexion',
                'Date création'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            parents = ParentUser.objects.all().prefetch_related('students')
            
            for parent in parents:
                writer.writerow({
                    'ID': parent.id,
                    'Parent ID': parent.parent_id,
                    'Nom': parent.last_name,
                    'Prénom': parent.first_name,
                    'Email': parent.email,
                    'Téléphone': parent.phone,
                    'Rôle': parent.get_role_display(),
                    'Statut': 'Actif' if parent.is_active else 'Inactif',
                    'Vérifié': 'Oui' if parent.is_verified else 'Non',
                    'Étudiants': parent.students.count(),
                    'Dernière connexion': parent.last_login.strftime('%d/%m/%Y %H:%M') if parent.last_login else 'Jamais',
                    'Date création': parent.created_at.strftime('%d/%m/%Y %H:%M'),
                })
        
        logger.info(f"Export CSV réussi vers {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur export CSV: {str(e)}")
        return False
