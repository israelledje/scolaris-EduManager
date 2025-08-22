from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from datetime import datetime, timedelta
import logging

from .models import (
    ParentUser, ParentStudentRelation, ParentPaymentMethod,
    ParentPayment, ParentNotification, ParentLoginSession
)
from students.models import Student, Guardian
from finances.models import (
    FeeTranche, TranchePayment, FeeStructure, InscriptionPayment,
    ExtraFee, ExtraFeePayment, FeeDiscount, Moratorium
)
from notes.models import Bulletin, Evaluation
from classes.models import SchoolClass
from school.models import SchoolYear

logger = logging.getLogger(__name__)

class ParentPortalService:
    """Service principal pour la gestion du portail parents"""

    @staticmethod
    def create_parent_account(guardian):
        """
        Crée automatiquement un compte parent pour un guardian
        """
        try:
            # Vérifier que le guardian n'a pas déjà un compte
            if ParentUser.objects.filter(email=guardian.email).exists():
                raise Exception("Ce parent a déjà un compte dans le portail.")

            # Générer un nom d'utilisateur unique
            username = ParentPortalService._generate_unique_username(guardian)

            # Créer l'utilisateur parent
            parent_user = ParentUser.objects.create(
                username=username,
                email=guardian.email,
                first_name=guardian.name.split()[0] if guardian.name else '',
                last_name=' '.join(guardian.name.split()[1:]) if guardian.name and len(guardian.name.split()) > 1 else '',
                phone=guardian.phone,
                role='PARENT' if guardian.relation in ['Père', 'Mère'] else 'GUARDIAN'
            )

            # Créer les relations avec les étudiants
            ParentPortalService._create_student_relations(parent_user, guardian)

            # Générer et envoyer le mot de passe temporaire
            temporary_password = parent_user.generate_temporary_password()
            parent_user.set_password(temporary_password)
            parent_user.save()

            # Envoyer les identifiants par email
            if parent_user.send_credentials_email(temporary_password):
                logger.info(f"Compte parent créé avec succès pour {guardian.email}")
                return parent_user
            else:
                # Si l'email échoue, supprimer le compte
                parent_user.delete()
                raise Exception("Impossible d'envoyer l'email avec les identifiants.")

        except Exception as e:
            logger.error(f"Erreur création compte parent: {str(e)}")
            raise e

    @staticmethod
    def _generate_unique_username(guardian):
        """Génère un nom d'utilisateur unique basé sur le nom du guardian"""
        base_username = guardian.name.lower().replace(' ', '').replace('-', '').replace("'", '')
        username = base_username[:15]  # Limiter à 15 caractères

        counter = 1
        original_username = username
        while ParentUser.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
            if counter > 999:
                # Fallback avec timestamp
                username = f"{original_username}{int(timezone.now().timestamp())}"
                break

        return username

    @staticmethod
    def _create_student_relations(parent_user, guardian):
        """Crée les relations entre le parent et ses étudiants"""
        try:
            # Créer la relation avec l'étudiant du guardian
            ParentStudentRelation.objects.create(
                parent_user=parent_user,
                student=guardian.student,
                relation_type=guardian.relation,
                is_active=True,
                can_view_academic=True,
                can_view_financial=True,
                can_make_payments=True
            )

            logger.info(f"Relation créée entre {parent_user.email} et {guardian.student}")
        except Exception as e:
            logger.error(f"Erreur création relation: {str(e)}")
            raise e

    @staticmethod
    def get_parent_statistics(parent_user):
        """Récupère les statistiques du parent"""
        try:
            students = ParentPortalService.get_parent_students(parent_user)

            # Calculer la moyenne des notes
            total_grades = 0
            grade_count = 0

            for student in students:
                grades = ParentPortalService.get_student_grades(student)
                if grades:
                    total_grades += sum(grades.values())
                    grade_count += len(grades)

            average_grade = round(total_grades / grade_count, 2) if grade_count > 0 else 0

            # Calculer les paiements en attente
            pending_payments = ParentPayment.objects.filter(
                parent_user=parent_user,
                status='PENDING'
            ).count()

            # Calculer les notifications non lues
            unread_notifications = ParentNotification.objects.filter(
                parent_user=parent_user,
                is_read=False
            ).count()

            return {
                'average_grade': average_grade,
                'pending_payments': pending_payments,
                'unread_notifications': unread_notifications,
            }
        except Exception as e:
            logger.error(f"Erreur calcul statistiques: {str(e)}")
            return {
                'average_grade': 0,
                'pending_payments': 0,
                'unread_notifications': 0,
            }

    @staticmethod
    def get_parent_students(parent_user):
        """Récupère tous les étudiants liés à un parent via les profils de tuteur"""
        # Utiliser la nouvelle relation Guardian-ParentUser
        students = []
        for guardian in parent_user.guardian_profiles.all():
            if guardian.student.is_active:
                students.append(guardian.student)
        return students

    @staticmethod
    def get_student_academic_info(student):
        """Récupère les informations académiques d'un étudiant"""
        try:
            current_year = timezone.now().year

            # Récupérer les bulletins
            bulletins = Bulletin.objects.filter(
                student=student,
                year=current_year
            ).order_by('-created_at')

            # Récupérer les notes récentes
            recent_grades = ParentPortalService.get_student_grades(student)

            # Récupérer la classe actuelle
            current_class = student.current_class if hasattr(student, 'current_class') else None

            return {
                'bulletins': bulletins,
                'recent_grades': recent_grades,
                'current_class': current_class,
                'current_year': current_year,
            }
        except Exception as e:
            logger.error(f"Erreur récupération infos académiques: {str(e)}")
            return {}

    @staticmethod
    def get_student_financial_info(student):
        """Récupère les informations financières d'un étudiant avec la nouvelle structure"""
        try:
            current_year = SchoolYear.objects.filter(is_active=True).first()
            if not current_year:
                current_year = SchoolYear.objects.order_by('-annee').first()
            
            if not current_year:
                return {}

            # Récupérer la structure des frais pour la classe de l'étudiant
            fee_structure = None
            if hasattr(student, 'current_class') and student.current_class:
                fee_structure = FeeStructure.objects.filter(
                    school_class=student.current_class,
                    year=current_year
                ).first()

            # Récupérer les tranches de frais
            tranches = []
            if fee_structure:
                tranches = FeeTranche.objects.filter(fee_structure=fee_structure).order_by('number')

            # Récupérer les paiements des tranches
            tranche_payments = TranchePayment.objects.filter(
                student=student,
                tranche__fee_structure__year=current_year
            )

            # Récupérer les paiements d'inscription
            inscription_payments = InscriptionPayment.objects.filter(
                student=student,
                fee_structure__year=current_year
            )

            # Récupérer les frais annexes et leurs paiements
            extra_fees = ExtraFee.objects.filter(
                year=current_year
            ).filter(
                Q(apply_to_all_classes=True) | 
                Q(classes=student.current_class) if hasattr(student, 'current_class') and student.current_class else Q()
            )

            extra_fee_payments = ExtraFeePayment.objects.filter(
                student=student,
                extra_fee__year=current_year
            )

            # Récupérer les remises
            discounts = FeeDiscount.objects.filter(
                student=student,
                tranche__fee_structure__year=current_year
            )

            # Calculer les totaux
            total_inscription_due = fee_structure.inscription_fee if fee_structure else 0
            total_inscription_paid = inscription_payments.aggregate(Sum('amount'))['amount__sum'] or 0
            
            total_tuition_due = sum(t.amount for t in tranches)
            total_tuition_paid = tranche_payments.aggregate(Sum('amount'))['amount__sum'] or 0
            
            total_extra_fees_due = sum(ef.get_amount_for_class(student.current_class) for ef in extra_fees)
            total_extra_fees_paid = extra_fee_payments.aggregate(Sum('amount'))['amount__sum'] or 0
            
            total_discounts = discounts.aggregate(Sum('amount'))['amount__sum'] or 0

            total_due = total_inscription_due + total_tuition_due + total_extra_fees_due
            total_paid = total_inscription_paid + total_tuition_paid + total_extra_fees_paid
            total_remaining = total_due - total_paid - total_discounts

            return {
                'fee_structure': fee_structure,
                'tranches': tranches,
                'tranche_payments': tranche_payments,
                'inscription_payments': inscription_payments,
                'extra_fees': extra_fees,
                'extra_fee_payments': extra_fee_payments,
                'discounts': discounts,
                'total_inscription_due': total_inscription_due,
                'total_inscription_paid': total_inscription_paid,
                'total_tuition_due': total_tuition_due,
                'total_tuition_paid': total_tuition_paid,
                'total_extra_fees_due': total_extra_fees_due,
                'total_extra_fees_paid': total_extra_fees_paid,
                'total_due': total_due,
                'total_paid': total_paid,
                'total_discounts': total_discounts,
                'total_remaining': max(total_remaining, 0),
            }
        except Exception as e:
            logger.error(f"Erreur récupération infos financières: {str(e)}")
            return {}

    @staticmethod
    def get_detailed_financial_overview(parent_user, current_year, filters=None):
        """Récupère la vue d'ensemble financière détaillée avec la nouvelle structure"""
        try:
            students = ParentPortalService.get_parent_students(parent_user)
            
            financial_data = {
                'students': [],
                'total_inscription_due': 0,
                'total_inscription_paid': 0,
                'total_tuition_due': 0,
                'total_tuition_paid': 0,
                'total_extra_fees_due': 0,
                'total_extra_fees_paid': 0,
                'total_due': 0,
                'total_paid': 0,
                'total_discounts': 0,
                'total_remaining': 0,
            }

            for student in students:
                financial_info = ParentPortalService.get_student_financial_info(student)
                
                # Ajouter les données de l'étudiant
                student_data = {
                    'student': student,
                    'financial_info': financial_info,
                    'tranches_status': ParentPortalService.get_student_tranches_status(student, current_year),
                    'extra_fees_status': ParentPortalService.get_student_extra_fees_status(student, current_year),
                }
                
                financial_data['students'].append(student_data)

                # Accumuler les totaux
                financial_data['total_inscription_due'] += financial_info.get('total_inscription_due', 0)
                financial_data['total_inscription_paid'] += financial_info.get('total_inscription_paid', 0)
                financial_data['total_tuition_due'] += financial_info.get('total_tuition_due', 0)
                financial_data['total_tuition_paid'] += financial_info.get('total_tuition_paid', 0)
                financial_data['total_extra_fees_due'] += financial_info.get('total_extra_fees_due', 0)
                financial_data['total_extra_fees_paid'] += financial_info.get('total_extra_fees_paid', 0)
                financial_data['total_due'] += financial_info.get('total_due', 0)
                financial_data['total_paid'] += financial_info.get('total_paid', 0)
                financial_data['total_discounts'] += financial_info.get('total_discounts', 0)
                financial_data['total_remaining'] += financial_info.get('total_remaining', 0)

            return financial_data
        except Exception as e:
            logger.error(f"Erreur récupération vue financière détaillée: {str(e)}")
            return {}

    @staticmethod
    def get_student_detailed_financial_info(student, current_year):
        """Récupère les informations financières détaillées d'un étudiant"""
        try:
            financial_info = ParentPortalService.get_student_financial_info(student)
            
            # Ajouter le statut détaillé des tranches
            tranches_status = ParentPortalService.get_student_tranches_status(student, current_year)
            
            # Ajouter le statut des frais annexes
            extra_fees_status = ParentPortalService.get_student_extra_fees_status(student, current_year)
            
            # Ajouter l'historique des paiements
            payment_history = ParentPortalService.get_student_payment_history(student, current_year)
            
            return {
                **financial_info,
                'tranches_status': tranches_status,
                'extra_fees_status': extra_fees_status,
                'payment_history': payment_history,
            }
        except Exception as e:
            logger.error(f"Erreur récupération infos financières détaillées: {str(e)}")
            return {}

    @staticmethod
    def get_student_tranches_status(student, current_year):
        """Récupère le statut détaillé des tranches pour un étudiant"""
        try:
            if not hasattr(student, 'current_class') or not student.current_class:
                return []

            fee_structure = FeeStructure.objects.filter(
                school_class=student.current_class,
                year=current_year
            ).first()

            if not fee_structure:
                return []

            tranches = FeeTranche.objects.filter(fee_structure=fee_structure).order_by('number')
            today = timezone.now().date()
            
            tranches_status = []
            for tranche in tranches:
                # Récupérer les paiements pour cette tranche
                payments = TranchePayment.objects.filter(
                    student=student,
                    tranche=tranche
                )
                total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
                
                # Récupérer les remises pour cette tranche
                discounts = FeeDiscount.objects.filter(
                    student=student,
                    tranche=tranche
                )
                total_discounts = discounts.aggregate(Sum('amount'))['amount__sum'] or 0
                
                # Calculer le reste à payer
                remaining = tranche.amount - total_paid - total_discounts
                
                # Déterminer le statut
                if total_paid + total_discounts >= tranche.amount:
                    status = 'PAID'
                elif tranche.due_date < today:
                    status = 'OVERDUE'
                elif total_paid > 0:
                    status = 'PARTIAL'
                else:
                    status = 'PENDING'
                
                # Calculer les jours jusqu'à l'échéance
                days_until_due = (tranche.due_date - today).days
                
                tranches_status.append({
                    'tranche': tranche,
                    'amount': tranche.amount,
                    'paid': total_paid,
                    'discounts': total_discounts,
                    'remaining': max(remaining, 0),
                    'status': status,
                    'due_date': tranche.due_date,
                    'days_until_due': days_until_due,
                    'payments': payments,
                    'discounts': discounts,
                })
            
            return tranches_status
        except Exception as e:
            logger.error(f"Erreur récupération statut tranches: {str(e)}")
            return []

    @staticmethod
    def get_student_extra_fees_status(student, current_year):
        """Récupère le statut des frais annexes pour un étudiant"""
        try:
            extra_fees = ExtraFee.objects.filter(
                year=current_year
            ).filter(
                Q(apply_to_all_classes=True) | 
                Q(classes=student.current_class) if hasattr(student, 'current_class') and student.current_class else Q()
            )
            
            extra_fees_status = []
            for extra_fee in extra_fees:
                # Récupérer le paiement pour ce frais annexe
                payment = ExtraFeePayment.objects.filter(
                    student=student,
                    extra_fee=extra_fee
                ).first()
                
                # Calculer le montant dû pour la classe de l'étudiant
                amount_due = extra_fee.get_amount_for_class(student.current_class) if hasattr(student, 'current_class') and student.current_class else extra_fee.amount
                
                # Déterminer le statut
                if payment:
                    status = 'PAID'
                elif extra_fee.due_date and extra_fee.due_date < timezone.now().date():
                    status = 'OVERDUE'
                else:
                    status = 'PENDING'
                
                extra_fees_status.append({
                    'extra_fee': extra_fee,
                    'amount_due': amount_due,
                    'payment': payment,
                    'status': status,
                    'due_date': extra_fee.due_date,
                })
            
            return extra_fees_status
        except Exception as e:
            logger.error(f"Erreur récupération statut frais annexes: {str(e)}")
            return []

    @staticmethod
    def get_student_payment_history(student, current_year):
        """Récupère l'historique des paiements d'un étudiant"""
        try:
            # Paiements des tranches
            tranche_payments = TranchePayment.objects.filter(
                student=student,
                tranche__fee_structure__year=current_year
            ).select_related('tranche', 'tranche__fee_structure')
            
            # Paiements d'inscription
            inscription_payments = InscriptionPayment.objects.filter(
                student=student,
                fee_structure__year=current_year
            ).select_related('fee_structure')
            
            # Paiements des frais annexes
            extra_fee_payments = ExtraFeePayment.objects.filter(
                student=student,
                extra_fee__year=current_year
            ).select_related('extra_fee')
            
            # Combiner et trier tous les paiements
            all_payments = []
            
            for payment in tranche_payments:
                all_payments.append({
                    'type': 'tranche',
                    'payment': payment,
                    'description': f"Tranche {payment.tranche.number} - {payment.tranche.fee_structure.school_class.name}",
                    'amount': payment.amount,
                    'date': payment.payment_date,
                    'mode': payment.mode,
                })
            
            for payment in inscription_payments:
                all_payments.append({
                    'type': 'inscription',
                    'payment': payment,
                    'description': f"Frais d'inscription - {payment.fee_structure.school_class.name}",
                    'amount': payment.amount,
                    'date': payment.payment_date,
                    'mode': payment.mode,
                })
            
            for payment in extra_fee_payments:
                all_payments.append({
                    'type': 'extra_fee',
                    'payment': payment,
                    'description': f"Frais annexe - {payment.extra_fee.name}",
                    'amount': payment.amount,
                    'date': payment.payment_date,
                    'mode': payment.mode,
                })
            
            # Trier par date (plus récent en premier)
            all_payments.sort(key=lambda x: x['date'], reverse=True)
            
            return all_payments
        except Exception as e:
            logger.error(f"Erreur récupération historique paiements: {str(e)}")
            return []

    @staticmethod
    def get_financial_reports(parent_user, current_year, student_filter=None):
        """Récupère les rapports financiers détaillés"""
        try:
            students = ParentPortalService.get_parent_students(parent_user)
            
            if student_filter:
                students = students.filter(
                    Q(first_name__icontains=student_filter) |
                    Q(last_name__icontains=student_filter) |
                    Q(matricule__icontains=student_filter)
                )
            
            reports = []
            for student in students:
                financial_info = ParentPortalService.get_student_financial_info(student)
                tranches_status = ParentPortalService.get_student_tranches_status(student, current_year)
                extra_fees_status = ParentPortalService.get_student_extra_fees_status(student, current_year)
                
                reports.append({
                    'student': student,
                    'financial_info': financial_info,
                    'tranches_status': tranches_status,
                    'extra_fees_status': extra_fees_status,
                })
            
            return reports
        except Exception as e:
            logger.error(f"Erreur récupération rapports financiers: {str(e)}")
            return []

    @staticmethod
    def get_upcoming_payments(parent_user, limit=5):
        """Récupère les prochains paiements"""
        try:
            students = ParentPortalService.get_parent_students(parent_user)

            upcoming_payments = []
            for student in students:
                if hasattr(student, 'current_class') and student.current_class:
                    fee_structures = FeeStructure.objects.filter(
                        school_class=student.current_class
                    )

                    for fee_structure in fee_structures:
                        if fee_structure.due_date > timezone.now().date():
                            upcoming_payments.append({
                                'student': student,
                                'fee_structure': fee_structure,
                                'due_date': fee_structure.due_date,
                                'amount': fee_structure.amount,
                            })

            # Trier par date d'échéance et limiter
            upcoming_payments.sort(key=lambda x: x['due_date'])
            return upcoming_payments[:limit]
        except Exception as e:
            logger.error(f"Erreur récupération paiements à venir: {str(e)}")
            return []

    @staticmethod
    def get_recent_notifications(parent_user, limit=5):
        """Récupère les notifications récentes"""
        try:
            return ParentNotification.objects.filter(
                parent_user=parent_user
            ).order_by('-created_at')[:limit]
        except Exception as e:
            logger.error(f"Erreur récupération notifications: {str(e)}")
            return []

class PaymentService:
    """Service pour la gestion des paiements avec la nouvelle structure"""

    @staticmethod
    def create_tranche_payment(parent_user, student, tranche, payment_method, amount):
        """Crée un nouveau paiement de tranche"""
        try:
            payment = ParentPayment.objects.create(
                parent_user=parent_user,
                student=student,
                tranche=tranche,
                payment_method=payment_method,
                amount=amount,
                method_type=payment_method.method_type,
                status='PENDING',
                total_amount=amount,
            )

            # Créer une notification
            ParentNotification.objects.create(
                parent_user=parent_user,
                title="Nouveau paiement de tranche initié",
                message=f"Paiement de {amount} FCFA pour {student} - Tranche {tranche.number}",
                notification_type='PAYMENT',
                related_student=student,
            )

            logger.info(f"Paiement de tranche créé: {payment.id}")
            return payment
        except Exception as e:
            logger.error(f"Erreur création paiement de tranche: {str(e)}")
            raise e

    @staticmethod
    def create_inscription_payment(parent_user, student, fee_structure, payment_method, amount):
        """Crée un nouveau paiement d'inscription"""
        try:
            payment = ParentPayment.objects.create(
                parent_user=parent_user,
                student=student,
                tranche=None,  # Pas de tranche pour l'inscription
                payment_method=payment_method,
                amount=amount,
                method_type=payment_method.method_type,
                status='PENDING',
                total_amount=amount,
            )

            # Créer une notification
            ParentNotification.objects.create(
                parent_user=parent_user,
                title="Nouveau paiement d'inscription initié",
                message=f"Paiement des frais d'inscription de {amount} FCFA pour {student}",
                notification_type='PAYMENT',
                related_student=student,
            )

            logger.info(f"Paiement d'inscription créé: {payment.id}")
            return payment
        except Exception as e:
            logger.error(f"Erreur création paiement d'inscription: {str(e)}")
            raise e

    @staticmethod
    def create_extra_fee_payment(parent_user, student, extra_fee, payment_method, amount):
        """Crée un nouveau paiement de frais annexe"""
        try:
            payment = ParentPayment.objects.create(
                parent_user=parent_user,
                student=student,
                tranche=None,  # Pas de tranche pour les frais annexes
                payment_method=payment_method,
                amount=amount,
                method_type=payment_method.method_type,
                status='PENDING',
                total_amount=amount,
            )

            # Créer une notification
            ParentNotification.objects.create(
                parent_user=parent_user,
                title="Nouveau paiement de frais annexe initié",
                message=f"Paiement du frais annexe '{extra_fee.name}' de {amount} FCFA pour {student}",
                notification_type='PAYMENT',
                related_student=student,
            )

            logger.info(f"Paiement de frais annexe créé: {payment.id}")
            return payment
        except Exception as e:
            logger.error(f"Erreur création paiement de frais annexe: {str(e)}")
            raise e

    @staticmethod
    def process_payment(payment):
        """Traite un paiement (simulation)"""
        try:
            # Simuler le traitement selon la méthode de paiement
            if payment.payment_method.method_type == 'OM':
                success = PaymentService._simulate_om_payment(payment)
            elif payment.payment_method.method_type == 'MOMO':
                success = PaymentService._simulate_momo_payment(payment)
            else:
                success = PaymentService._simulate_card_payment(payment)

            if success:
                payment.status = 'COMPLETED'
                payment.completed_at = timezone.now()
                payment.save()

                # Créer une notification de succès
                ParentNotification.objects.create(
                    parent_user=payment.parent_user,
                    title="Paiement confirmé",
                    message=f"Votre paiement de {payment.amount} FCFA a été confirmé",
                    notification_type='PAYMENT_SUCCESS',
                    related_id=payment.id,
                )

                logger.info(f"Paiement traité avec succès: {payment.id}")
                return True
            else:
                payment.status = 'FAILED'
                payment.save()

                # Créer une notification d'échec
                ParentNotification.objects.create(
                    parent_user=payment.parent_user,
                    title="Paiement échoué",
                    message=f"Votre paiement de {payment.amount} FCFA a échoué",
                    notification_type='PAYMENT_FAILED',
                    related_id=payment.id,
                )

                logger.error(f"Paiement échoué: {payment.id}")
                return False

        except Exception as e:
            logger.error(f"Erreur traitement paiement: {str(e)}")
            payment.status = 'FAILED'
            payment.save()
            return False

    @staticmethod
    def _simulate_om_payment(payment):
        """Simule un paiement Orange Money"""
        import random
        # Simulation avec 95% de succès
        return random.random() > 0.05

    @staticmethod
    def _simulate_momo_payment(payment):
        """Simule un paiement MTN Mobile Money"""
        import random
        # Simulation avec 95% de succès
        return random.random() > 0.05

    @staticmethod
    def _simulate_card_payment(payment):
        """Simule un paiement par carte"""
        import random
        # Simulation avec 90% de succès
        return random.random() > 0.10

    @staticmethod
    def process_payment_webhook(data):
        """Traite un webhook de paiement"""
        try:
            # Traiter les données du webhook selon le fournisseur
            payment_id = data.get('payment_id')
            status = data.get('status')

            if payment_id and status:
                # Mettre à jour le statut du paiement
                payment = ParentPayment.objects.get(transaction_id=payment_id)
                payment.status = 'COMPLETED' if status == 'success' else 'FAILED'
                payment.completed_at = timezone.now()
                payment.save()

                logger.info(f"Webhook traité: {payment_id} -> {status}")
                return status

            return 'unknown'
        except Exception as e:
            logger.error(f"Erreur traitement webhook: {str(e)}")
            return 'error'
