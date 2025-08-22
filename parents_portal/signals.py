from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import ParentUser, ParentStudentRelation, ParentPayment, ParentNotification
from students.models import Guardian, Student
from notes.models import Bulletin
from finances.models import TranchePayment

@receiver(post_save, sender=Guardian)
def create_parent_account_on_guardian_creation(sender, instance, created, **kwargs):
    """
    Crée automatiquement un compte parent quand un guardian est créé
    """
    if created and instance.email:
        try:
            from .services import ParentPortalService
            ParentPortalService.create_parent_account(instance)
        except Exception as e:
            print(f"Erreur création compte parent automatique: {e}")

@receiver(post_save, sender=Bulletin)
def notify_parents_on_bulletin_creation(sender, instance, created, **kwargs):
    """
    Notifie automatiquement les parents quand un bulletin est créé
    """
    if created:
        try:
            # Récupérer tous les parents de l'étudiant
            parent_relations = ParentStudentRelation.objects.filter(
                student=instance.student,
                can_view_grades=True
            )
            
            for relation in parent_relations:
                ParentNotification.objects.create(
                    parent=relation.parent,
                    notification_type='BULLETIN',
                    title='Nouveau bulletin disponible',
                    message=f'Le bulletin de {instance.student.first_name} {instance.student.last_name} pour la {instance.sequence} est maintenant disponible.',
                    related_student=instance.student,
                    related_url=f'/parents/bulletins/{instance.id}/'
                )
                
                # Envoyer un email de notification
                if relation.parent.email:
                    try:
                        send_mail(
                            subject='Nouveau bulletin disponible',
                            message=f"""
                            Bonjour {relation.parent.get_full_name()},
                            
                            Le bulletin de {instance.student.first_name} {instance.student.last_name} 
                            pour la {instance.sequence} est maintenant disponible.
                            
                            Connectez-vous à votre portail parent pour le consulter.
                            
                            Cordialement,
                            L'équipe {getattr(settings, 'SITE_NAME', 'Scolaris')}
                            """,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[relation.parent.email],
                            fail_silently=True
                        )
                    except Exception as e:
                        print(f"Erreur envoi email bulletin: {e}")
                        
        except Exception as e:
            print(f"Erreur notification bulletin: {e}")

@receiver(post_save, sender=TranchePayment)
def notify_parents_on_payment_reception(sender, instance, created, **kwargs):
    """
    Notifie automatiquement les parents quand un paiement est reçu
    """
    if created:
        try:
            # Récupérer les parents de l'étudiant
            parent_relations = ParentStudentRelation.objects.filter(
                student=instance.student,
                can_view_finances=True
            )
            
            for relation in parent_relations:
                ParentNotification.objects.create(
                    parent=relation.parent,
                    notification_type='PAYMENT',
                    title='Paiement reçu',
                    message=f'Un paiement de {instance.amount} FCFA a été reçu pour {instance.student.first_name} {instance.student.last_name}.',
                    related_student=instance.student,
                    related_url=f'/parents/finances/'
                )
                
        except Exception as e:
            print(f"Erreur notification paiement: {e}")

@receiver(post_save, sender=Student)
def update_parent_relations_on_student_change(sender, instance, **kwargs):
    """
    Met à jour les relations parent-étudiant quand un étudiant change de classe
    """
    try:
        # Vécupérer les relations existantes
        relations = ParentStudentRelation.objects.filter(student=instance)
        
        for relation in relations:
            # Vérifier si la relation est toujours valide
            if not instance.is_active:
                # Désactiver les permissions si l'étudiant n'est plus actif
                relation.can_view_grades = False
                relation.can_view_finances = False
                relation.can_make_payments = False
                relation.can_view_attendance = False
                relation.save()
                
        # Créer des notifications pour les changements importants
        if instance.current_class:
            for relation in relations:
                ParentNotification.objects.create(
                    parent=relation.parent,
                    notification_type='GENERAL',
                    title='Changement de classe',
                    message=f'{instance.first_name} {instance.last_name} a été affecté(e) à la classe {instance.current_class.name}.',
                    related_student=instance
                )
                
    except Exception as e:
        print(f"Erreur mise à jour relations: {e}")

@receiver(post_delete, sender=ParentStudentRelation)
def cleanup_on_relation_deletion(sender, instance, **kwargs):
    """
    Nettoie les données associées quand une relation parent-étudiant est supprimée
    """
    try:
        # Supprimer les notifications associées
        ParentNotification.objects.filter(
            parent=instance.parent,
            related_student=instance.student
        ).delete()
        
        # Vérifier si le parent a encore des étudiants
        if not instance.parent.students.exists():
            # Désactiver le compte parent s'il n'a plus d'étudiants
            instance.parent.is_active = False
            instance.parent.save()
            
            # Créer une notification d'information
            ParentNotification.objects.create(
                parent=instance.parent,
                notification_type='GENERAL',
                title='Compte désactivé',
                message='Votre compte a été désactivé car vous n\'avez plus d\'étudiants associés.',
                related_student=None
            )
            
    except Exception as e:
        print(f"Erreur nettoyage relation: {e}")

@receiver(post_save, sender=ParentPayment)
def handle_payment_status_change(sender, instance, **kwargs):
    """
    Gère les changements de statut des paiements
    """
    try:
        if instance.status == 'COMPLETED':
            # Créer une notification de succès
            ParentNotification.objects.create(
                parent=instance.parent,
                notification_type='PAYMENT',
                title='Paiement confirmé',
                message=f'Votre paiement de {instance.amount} FCFA pour {instance.student.first_name} {instance.student.last_name} a été confirmé avec succès.',
                related_student=instance.student,
                related_url=f'/parents/finances/payment/success/{instance.id}/'
            )
            
        elif instance.status == 'FAILED':
            # Créer une notification d'échec
            ParentNotification.objects.create(
                parent=instance.parent,
                notification_type='PAYMENT',
                title='Paiement échoué',
                message=f'Votre paiement de {instance.amount} FCFA pour {instance.student.first_name} {instance.student.last_name} a échoué. Veuillez réessayer.',
                related_student=instance.student,
                related_url=f'/parents/finances/'
            )
            
    except Exception as e:
        print(f"Erreur gestion statut paiement: {e}")

# Signal pour les rappels de paiement automatiques
def send_payment_reminders():
    """
    Envoie des rappels de paiement aux parents (à exécuter via une tâche cron)
    """
    try:
        from datetime import timedelta
        from .services import ParentPortalService
        
        # Récupérer les échéances dans les 7 prochains jours
        reminder_date = timezone.now().date() + timedelta(days=7)
        
        # Récupérer tous les parents actifs
        active_parents = ParentUser.objects.filter(is_active=True)
        
        for parent in active_parents:
            upcoming_payments = ParentPortalService.get_upcoming_payments(parent)
            
            for payment_info in upcoming_payments:
                if payment_info['due_date'] <= reminder_date:
                    # Créer une notification de rappel
                    ParentNotification.objects.create(
                        parent=parent,
                        notification_type='REMINDER',
                        title='Rappel de paiement',
                        message=f'Rappel: Échéance de paiement le {payment_info["due_date"].strftime("%d/%m/%Y")} pour {payment_info["student"].first_name} {payment_info["student"].last_name} - Montant: {payment_info["amount"]} FCFA',
                        related_student=payment_info['student'],
                        related_url=f'/parents/finances/payment/{payment_info["student"].id}/{payment_info["tranche"].id}/'
                    )
                    
                    # Envoyer un email de rappel
                    if parent.email:
                        try:
                            send_mail(
                                subject='Rappel de paiement - Échéance proche',
                                message=f"""
                                Bonjour {parent.get_full_name()},
                                
                                Ceci est un rappel amical concernant l'échéance de paiement :
                                
                                Étudiant: {payment_info["student"].first_name} {payment_info["student"].last_name}
                                Échéance: {payment_info["due_date"].strftime("%d/%m/%Y")}
                                Montant: {payment_info["amount"]} FCFA
                                Tranche: {payment_info["tranche"].number}
                                
                                Connectez-vous à votre portail parent pour effectuer le paiement.
                                
                                Cordialement,
                                L'équipe {getattr(settings, 'SITE_NAME', 'Scolaris')}
                                """,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[parent.email],
                                fail_silently=True
                            )
                        except Exception as e:
                            print(f"Erreur envoi email rappel: {e}")
                            
    except Exception as e:
        print(f"Erreur envoi rappels: {e}")
