import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db import transaction, models
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from django.templatetags.static import static
from weasyprint.text.fonts import FontConfiguration
import json
import os
from datetime import datetime, timedelta

from .models import (
    FeeStructure, FeeTranche, TranchePayment, InscriptionPayment, FeeDiscount, 
    Moratorium, PaymentRefund, ExtraFee, ExtraFeeType, ExtraFeePayment
)

from .forms import (
    FeeStructureForm, FeeTrancheForm, TranchePaymentForm, InscriptionPaymentForm, FeeDiscountForm,
    MoratoriumForm, PaymentRefundForm, ExtraFeeForm, BulkTranchePaymentForm,
    FeeStructureSearchForm, PaymentSearchForm, ExtraFeeTypeForm, ExtraFeePaymentForm
)
from school.models import SchoolYear, School, CurrentSchoolYear
from classes.models import SchoolClass
from students.models import Student
from authentication.models import User

logger = logging.getLogger(__name__)


# ==================== VUES PRINCIPALES MANQUANTES ====================

@login_required
def financial_dashboard(request):
    """Vue pour le tableau de bord financier principal"""
    logger.info(f"Utilisateur {request.user} accède au tableau de bord financier")
    
    try:
        # Récupérer l'année scolaire actuelle
        current_year = CurrentSchoolYear.objects.first()
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('school:config_school')
        
        # Statistiques générales
        total_students = Student.objects.filter(
            current_class__year=current_year.year,
            is_active=True
        ).count()
        
        total_fee_structures = FeeStructure.objects.filter(year=current_year.year).count()
        
        # Paiements de l'année
        total_payments = TranchePayment.objects.filter(
            tranche__fee_structure__year=current_year.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_inscription_payments = InscriptionPayment.objects.filter(
            fee_structure__year=current_year.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_extra_fee_payments = ExtraFeePayment.objects.filter(
            extra_fee__year=current_year.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_revenue = total_payments + total_inscription_payments + total_extra_fee_payments
        
        # Calculer le total dû (basé sur les structures de frais)
        total_due = 0
        fee_structures = FeeStructure.objects.filter(year=current_year.year)
        for fs in fee_structures:
            # Nombre d'étudiants dans cette classe
            class_students = Student.objects.filter(
                current_class=fs.school_class,
                is_active=True
            ).count()
            # Montant total dû pour cette classe (inscription + scolarité)
            class_total = (fs.inscription_fee + fs.tuition_total) * class_students
            total_due += class_total
        
        # Calculer le taux de recouvrement
        recovery_rate = 0
        if total_due > 0:
            recovery_rate = (total_revenue / total_due) * 100
        
        # Calculer le reste à payer et les pourcentages
        total_remaining = total_due - total_revenue
        remaining_percentage = 0
        if total_due > 0:
            remaining_percentage = (total_remaining / total_due) * 100
        
        # Récupérer les remises
        total_discounts = FeeDiscount.objects.filter(
            tranche__fee_structure__year=current_year.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        discount_percentage = 0
        if total_revenue > 0:
            discount_percentage = (total_discounts / total_revenue) * 100
        
        # Paiements en retard
        overdue_payments = TranchePayment.objects.filter(
            tranche__fee_structure__year=current_year.year,
            tranche__due_date__lt=timezone.now().date(),
            amount__lt=models.F('tranche__amount')
        ).count()
        
        # Moratoires en attente
        pending_moratoriums = Moratorium.objects.filter(
            student__current_class__year=current_year.year,
            is_approved=False
        ).count()
        
        # Récupérer les derniers paiements (5 plus récents)
        recent_payments = []
        
        # Derniers paiements de tranches
        recent_tranche_payments = TranchePayment.objects.filter(
            tranche__fee_structure__year=current_year.year
        ).select_related('student', 'tranche').order_by('-created_at')[:5]
        
        for payment in recent_tranche_payments:
            recent_payments.append({
                'payment': payment,
                'amount': payment.amount,
                'date': payment.payment_date,
                'description': f"Tranche {payment.tranche.number}",
                'student': payment.student
            })
        
        # Derniers paiements d'inscription
        recent_inscription_payments = InscriptionPayment.objects.filter(
            fee_structure__year=current_year.year
        ).select_related('student').order_by('-created_at')[:5]
        
        for payment in recent_inscription_payments:
            recent_payments.append({
                'payment': payment,
                'amount': payment.amount,
                'date': payment.payment_date,
                'description': "Frais d'inscription",
                'student': payment.student
            })
        
        # Trier par date et prendre les 5 plus récents
        recent_payments.sort(key=lambda x: x['date'], reverse=True)
        recent_payments = recent_payments[:5]
        
        # Données pour les graphiques
        # Paiements par mode
        payments_by_mode = TranchePayment.objects.filter(
            tranche__fee_structure__year=current_year.year
        ).values('mode').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Paiements par mois (6 derniers mois)
        payments_by_month = []
        for i in range(6):
            month_date = timezone.now().date() - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            month_total = TranchePayment.objects.filter(
                tranche__fee_structure__year=current_year.year,
                payment_date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            payments_by_month.append({
                'month_name': month_start.strftime('%b %Y'),
                'total': month_total
            })
        
        payments_by_month.reverse()  # Plus ancien au plus récent
        
        context = {
            'current_year': current_year.year,
            'total_students': total_students,
            'total_fee_structures': total_fee_structures,
            'total_revenue': total_revenue,
            'total_all_payments': total_revenue,  # Alias pour le template
            'total_due': total_due,
            'total_remaining': total_remaining,
            'recovery_rate': recovery_rate,
            'remaining_percentage': remaining_percentage,
            'total_discounts': total_discounts,
            'discount_percentage': discount_percentage,
            'overdue_payments': overdue_payments,
            'pending_moratoriums': pending_moratoriums,
            'total_payments': total_payments,
            'total_inscription_payments': total_inscription_payments,
            'total_extra_fee_payments': total_extra_fee_payments,
            'recent_payments': recent_payments,
            'payments_by_mode': payments_by_mode,
            'payments_by_month': payments_by_month,
        }
        
        return render(request, 'finances/financial_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du tableau de bord financier: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du tableau de bord.")
        return redirect('dashboard:dashboard')


@login_required
def student_financial_status(request, student_pk):
    """Vue pour afficher le statut financier d'un étudiant"""
    logger.info(f"Utilisateur {request.user} consulte le statut financier de l'étudiant {student_pk}")
    
    try:
        student = get_object_or_404(Student, pk=student_pk, is_active=True)
        
        # Récupérer l'année scolaire actuelle
        current_year = CurrentSchoolYear.objects.first()
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('school:config_school')
        
        # Structure de frais de l'étudiant
        fee_structure = FeeStructure.objects.filter(
            school_class=student.current_class,
            year=current_year.year
        ).first()
        
        if not fee_structure:
            messages.warning(request, f"Aucune structure de frais trouvée pour {student.current_class} - {current_year.year.annee}")
            return redirect('finances:financial_dashboard')
        
        # Paiements de tranches
        tranche_payments = TranchePayment.objects.filter(
            student=student,
            tranche__fee_structure=fee_structure
        ).select_related('tranche').order_by('tranche__number')
        
        # Paiement d'inscription
        inscription_payment = InscriptionPayment.objects.filter(
            student=student,
            fee_structure=fee_structure
        ).first()
        
        # Frais annexes
        extra_fee_payments = ExtraFeePayment.objects.filter(
            student=student,
            extra_fee__year=current_year.year
        ).select_related('extra_fee')
        
        # Remises et bourses
        discounts = FeeDiscount.objects.filter(
            student=student,
            tranche__fee_structure=fee_structure
        ).select_related('tranche')
        
        # Moratoires
        moratoriums = Moratorium.objects.filter(
            student=student,
            tranche__fee_structure=fee_structure
        ).select_related('tranche')
        
        context = {
            'student': student,
            'current_year': current_year.year,
            'fee_structure': fee_structure,
            'tranche_payments': tranche_payments,
            'inscription_payment': inscription_payment,
            'extra_fee_payments': extra_fee_payments,
            'discounts': discounts,
            'moratoriums': moratoriums,
        }
        
        return render(request, 'finances/student_financial_status.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du statut financier de l'étudiant {student_pk}: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du statut financier.")
        return redirect('finances:financial_dashboard')


@login_required
def reports_dashboard(request):
    """Vue pour le tableau de bord des rapports"""
    logger.info(f"Utilisateur {request.user} accède au tableau de bord des rapports")
    
    try:
        current_year = CurrentSchoolYear.objects.first()
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('school:config_school')
        
        context = {
            'current_year': current_year.year,
        }
        
        return render(request, 'finances/reports_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du tableau de bord des rapports: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage des rapports.")
        return redirect('finances:financial_dashboard')


@login_required
def inscriptions_report(request):
    """Rapport des inscriptions"""
    logger.info(f"Utilisateur {request.user} consulte le rapport des inscriptions")
    
    try:
        current_year = CurrentSchoolYear.objects.first()
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:reports_dashboard')
        
        # Logique du rapport des inscriptions
        context = {
            'current_year': current_year.year,
        }
        
        return render(request, 'finances/inscriptions_report.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du rapport des inscriptions: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du rapport.")
        return redirect('finances:reports_dashboard')


@login_required
def inscriptions_report_class(request, class_id):
    """Rapport des inscriptions par classe"""
    logger.info(f"Utilisateur {request.user} consulte le rapport des inscriptions pour la classe {class_id}")
    
    try:
        school_class = get_object_or_404(SchoolClass, pk=class_id)
        current_year = CurrentSchoolYear.objects.first()
        
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:reports_dashboard')
        
        context = {
            'school_class': school_class,
            'current_year': current_year.year,
        }
        
        return render(request, 'finances/inscriptions_report_class.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du rapport des inscriptions pour la classe {class_id}: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du rapport.")
        return redirect('finances:reports_dashboard')


@login_required
def export_inscriptions_report(request):
    """Export PDF du rapport des inscriptions"""
    logger.info(f"Utilisateur {request.user} exporte le rapport des inscriptions")
    
    try:
        # Logique d'export PDF
        return HttpResponse("Export PDF des inscriptions - À implémenter")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export du rapport des inscriptions: {e}")
        messages.error(request, "Une erreur est survenue lors de l'export du rapport.")
        return redirect('finances:inscriptions_report')


@login_required
def tuition_report(request):
    """Rapport des scolarités"""
    logger.info(f"Utilisateur {request.user} consulte le rapport des scolarités")
    
    try:
        current_year = CurrentSchoolYear.objects.first()
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:reports_dashboard')
        
        context = {
            'current_year': current_year.year,
        }
        
        return render(request, 'finances/tuition_report.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du rapport des scolarités: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du rapport.")
        return redirect('finances:reports_dashboard')


@login_required
def tuition_report_class(request, class_id):
    """Rapport des scolarités par classe"""
    logger.info(f"Utilisateur {request.user} consulte le rapport des scolarités pour la classe {class_id}")
    
    try:
        school_class = get_object_or_404(SchoolClass, pk=class_id)
        current_year = CurrentSchoolYear.objects.first()
        
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:reports_dashboard')
        
        context = {
            'school_class': school_class,
            'current_year': current_year.year,
        }
        
        return render(request, 'finances/tuition_report_class.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du rapport des scolarités pour la classe {class_id}: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du rapport.")
        return redirect('finances:reports_dashboard')


@login_required
def export_tuition_report(request):
    """Export PDF du rapport des scolarités"""
    logger.info(f"Utilisateur {request.user} exporte le rapport des scolarités")
    
    try:
        # Logique d'export PDF
        return HttpResponse("Export PDF des scolarités - À implémenter")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export du rapport des scolarités: {e}")
        messages.error(request, "Une erreur est survenue lors de l'export du rapport.")
        return redirect('finances:tuition_report')


@login_required
def overdue_report(request):
    """Rapport des paiements en retard"""
    logger.info(f"Utilisateur {request.user} consulte le rapport des paiements en retard")
    
    try:
        current_year = CurrentSchoolYear.objects.first()
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:reports_dashboard')
        
        context = {
            'current_year': current_year.year,
        }
        
        return render(request, 'finances/overdue_report.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du rapport des paiements en retard: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du rapport.")
        return redirect('finances:reports_dashboard')


@login_required
def overdue_report_class(request, class_id):
    """Rapport des paiements en retard par classe"""
    logger.info(f"Utilisateur {request.user} consulte le rapport des paiements en retard pour la classe {class_id}")
    
    try:
        school_class = get_object_or_404(SchoolClass, pk=class_id)
        current_year = CurrentSchoolYear.objects.first()
        
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:reports_dashboard')
        
        context = {
            'school_class': school_class,
            'current_year': current_year.year,
        }
        
        return render(request, 'finances/overdue_report_class.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du rapport des paiements en retard pour la classe {class_id}: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du rapport.")
        return redirect('finances:reports_dashboard')


@login_required
def export_overdue_report(request):
    """Export PDF du rapport des paiements en retard"""
    logger.info(f"Utilisateur {request.user} exporte le rapport des paiements en retard")
    
    try:
        # Logique d'export PDF
        return HttpResponse("Export PDF des paiements en retard - À implémenter")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export du rapport des paiements en retard: {e}")
        messages.error(request, "Une erreur est survenue lors de l'export du rapport.")
        return redirect('finances:overdue_report')


@login_required
def performance_report(request):
    """Rapport de performance financière"""
    logger.info(f"Utilisateur {request.user} consulte le rapport de performance financière")
    
    try:
        current_year = CurrentSchoolYear.objects.first()
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:reports_dashboard')
        
        context = {
            'current_year': current_year.year,
        }
        
        return render(request, 'finances/performance_report.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du rapport de performance: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du rapport.")
        return redirect('finances:reports_dashboard')


@login_required
def export_performance_report(request):
    """Export PDF du rapport de performance"""
    logger.info(f"Utilisateur {request.user} exporte le rapport de performance")
    
    try:
        # Logique d'export PDF
        return HttpResponse("Export PDF de performance - À implémenter")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export du rapport de performance: {e}")
        messages.error(request, "Une erreur est survenue lors de l'export du rapport.")
        return redirect('finances:performance_report')


@login_required
def student_report(request, student_id):
    """Rapport financier d'un étudiant"""
    logger.info(f"Utilisateur {request.user} consulte le rapport financier de l'étudiant {student_id}")
    
    try:
        student = get_object_or_404(Student, pk=student_id, is_active=True)
        current_year = CurrentSchoolYear.objects.first()
        
        if not current_year:
            messages.warning(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:reports_dashboard')
        
        # Récupérer la structure de frais de l'étudiant
        fee_structure = FeeStructure.objects.filter(
            school_class=student.current_class,
            year=current_year.year
        ).first()
        
        # Calculer les totaux
        total_due = 0
        if fee_structure:
            total_due = fee_structure.inscription_fee + fee_structure.tuition_total
        
        # Paiements d'inscription
        inscription_payments = InscriptionPayment.objects.filter(
            student=student,
            fee_structure__year=current_year.year
        ).select_related('fee_structure')
        
        total_inscription_paid = inscription_payments.aggregate(
            total=Sum('amount'))['total'] or 0
        
        # Paiements de scolarité (tranches)
        tuition_payments = TranchePayment.objects.filter(
            student=student,
            tranche__fee_structure__year=current_year.year
        ).select_related('tranche', 'tranche__fee_structure')
        
        total_tuition_paid = tuition_payments.aggregate(
            total=Sum('amount'))['total'] or 0
        
        # Total payé
        total_paid = total_inscription_paid + total_tuition_paid
        
        # Reste à payer
        remaining = total_due - total_paid
        
        # Remises accordées
        discounts = FeeDiscount.objects.filter(
            student=student,
            tranche__fee_structure__year=current_year.year
        ).select_related('tranche')
        
        total_discounts = discounts.aggregate(
            total=Sum('amount'))['total'] or 0
        
        # Tranches à venir (non payées)
        upcoming_tranches = []
        if fee_structure:
            for tranche in fee_structure.tranches.all():
                # Vérifier si la tranche a été payée
                paid_amount = TranchePayment.objects.filter(
                    student=student,
                    tranche=tranche
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                if paid_amount < tranche.amount:
                    upcoming_tranches.append(tranche)
        
        # Date actuelle pour les comparaisons
        today = timezone.now().date()
        
        context = {
            'student': student,
            'current_year': current_year.year,
            'fee_structure': fee_structure,
            'total_due': total_due,
            'total_paid': total_paid,
            'remaining': remaining,
            'inscription_payments': inscription_payments,
            'tuition_payments': tuition_payments,
            'total_inscription_paid': total_inscription_paid,
            'total_tuition_paid': total_tuition_paid,
            'discounts': discounts,
            'total_discounts': total_discounts,
            'upcoming_tranches': upcoming_tranches,
            'today': today,
        }
        
        return render(request, 'finances/student_report.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage du rapport de l'étudiant {student_id}: {e}")
        messages.error(request, "Une erreur est survenue lors de l'affichage du rapport.")
        return redirect('finances:reports_dashboard')


@login_required
def export_student_report(request, student_id):
    """Export PDF du rapport d'un étudiant"""
    logger.info(f"Utilisateur {request.user} exporte le rapport de l'étudiant {student_id}")
    
    try:
        student = get_object_or_404(Student, pk=student_id, is_active=True)
        current_year = CurrentSchoolYear.objects.first()
        
        if not current_year:
            messages.error(request, "Aucune année scolaire n'est configurée comme année actuelle.")
            return redirect('finances:student_report', student_id=student_id)
        
        # Récupérer la structure de frais de l'étudiant
        fee_structure = FeeStructure.objects.filter(
            school_class=student.current_class,
            year=current_year.year
        ).first()
        
        # Calculer les totaux
        total_due = 0
        if fee_structure:
            total_due = fee_structure.inscription_fee + fee_structure.tuition_total
        
        # Paiements d'inscription
        inscription_payments = InscriptionPayment.objects.filter(
            student=student,
            fee_structure__year=current_year.year
        ).select_related('fee_structure')
        
        total_inscription_paid = inscription_payments.aggregate(
            total=Sum('amount'))['total'] or 0
        
        # Paiements de scolarité (tranches)
        tuition_payments = TranchePayment.objects.filter(
            student=student,
            tranche__fee_structure__year=current_year.year
        ).select_related('tranche', 'tranche__fee_structure')
        
        total_tuition_paid = tuition_payments.aggregate(
            total=Sum('amount'))['total'] or 0
        
        # Total payé
        total_paid = total_inscription_paid + total_tuition_paid
        
        # Reste à payer
        remaining = total_due - total_paid
        
        # Remises accordées
        discounts = FeeDiscount.objects.filter(
            student=student,
            tranche__fee_structure__year=current_year.year
        ).select_related('tranche')
        
        total_discounts = discounts.aggregate(
            total=Sum('amount'))['total'] or 0
        
        # Tranches à venir (non payées)
        upcoming_tranches = []
        if fee_structure:
            for tranche in fee_structure.tranches.all():
                # Vérifier si la tranche a été payée
                paid_amount = TranchePayment.objects.filter(
                    student=student,
                    tranche=tranche
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                if paid_amount < tranche.amount:
                    upcoming_tranches.append(tranche)
        
        # Date actuelle pour les comparaisons
        today = timezone.now().date()
        
        # Récupérer les informations de l'école
        try:
            from school.models import School
            school = School.objects.first()
            document_header = school.get_active_header() if school else None
            
            # Construire les URLs absolues pour les images
            school_logo_url = None
            school_signature_url = None
            if document_header:
                if document_header.logo:
                    try:
                        school_logo_url = request.build_absolute_uri(document_header.logo.url)
                    except Exception:
                        school_logo_url = None
                
                if document_header.signature:
                    try:
                        school_signature_url = request.build_absolute_uri(document_header.signature.url)
                    except Exception:
                        school_signature_url = None
        except:
            school = None
            document_header = None
            school_logo_url = None
            school_signature_url = None
        
        context = {
            'student': student,
            'current_year': current_year.year,
            'fee_structure': fee_structure,
            'total_due': total_due,
            'total_paid': total_paid,
            'remaining': remaining,
            'inscription_payments': inscription_payments,
            'tuition_payments': tuition_payments,
            'total_inscription_paid': total_inscription_paid,
            'total_tuition_paid': total_tuition_paid,
            'discounts': discounts,
            'total_discounts': total_discounts,
            'upcoming_tranches': upcoming_tranches,
            'today': today,
            'school': school,
            'document_header': document_header,
            'school_logo': school_logo_url,
            'school_signature': school_signature_url,
            'generated_at': timezone.now(),
        }
        
        # Générer le HTML
        html_string = render_to_string('finances/student_report_pdf.html', context)
        
        # Configuration des polices
        font_config = FontConfiguration()
        
        # Générer le PDF
        html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = html.write_pdf(
            stylesheets=[],
            font_config=font_config
        )
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_financier_{student.last_name}_{student.first_name}_{current_year.year.annee}.pdf"'
        
        logger.info(f"PDF du rapport financier généré pour l'étudiant {student} par {request.user}")
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export du rapport de l'étudiant {student_id}: {e}")
        messages.error(request, "Une erreur est survenue lors de l'export du rapport.")
        return redirect('finances:student_report', student_id=student_id)


@login_required
def get_tranches_for_class(request):
    """API AJAX pour récupérer les tranches d'une classe"""
    logger.info(f"Utilisateur {request.user} récupère les tranches pour une classe via AJAX")
    
    try:
        class_id = request.GET.get('class_id')
        if not class_id:
            return JsonResponse({'error': 'ID de classe manquant'}, status=400)
        
        school_class = get_object_or_404(SchoolClass, pk=class_id)
        
        # Récupérer les structures de frais de cette classe
        fee_structures = FeeStructure.objects.filter(school_class=school_class)
        
        tranches = []
        for structure in fee_structures:
            structure_tranches = structure.tranches.all()
            for tranche in structure_tranches:
                tranches.append({
                    'id': tranche.id,
                    'number': tranche.number,
                    'amount': float(tranche.amount),
                    'due_date': tranche.due_date.isoformat() if tranche.due_date else None,
                    'fee_structure': structure.id,
                    'fee_structure_name': f"{structure.school_class.name} - {structure.year.annee}"
                })
        
        return JsonResponse({'tranches': tranches})
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tranches pour la classe {class_id}: {e}")
        return JsonResponse({'error': 'Erreur lors de la récupération des tranches'}, status=500)


@login_required
def search_students(request):
    """API AJAX pour rechercher des étudiants"""
    logger.info(f"Utilisateur {request.user} recherche des étudiants via AJAX")
    
    try:
        query = request.GET.get('query', '')
        if len(query) < 2:
            return JsonResponse({'students': []})
        
        students = Student.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(matricule__icontains=query),
            is_active=True
        ).select_related('current_class')[:10]
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'matricule': student.matricule,
                'current_class': student.current_class.name if student.current_class else 'N/A'
            })
        
        return JsonResponse({'students': students_data})
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche d'étudiants: {e}")
        return JsonResponse({'error': 'Erreur lors de la recherche'}, status=500)


@login_required
def get_student_info(request):
    """API AJAX pour récupérer les informations d'un étudiant"""
    logger.info(f"Utilisateur {request.user} récupère les informations d'un étudiant via AJAX")
    
    try:
        student_id = request.GET.get('student_id')
        if not student_id:
            return JsonResponse({'error': 'ID d\'étudiant manquant'}, status=400)
        
        student = get_object_or_404(Student, pk=student_id, is_active=True)
        
        student_data = {
            'id': student.id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'matricule': student.matricule,
            'current_class': student.current_class.name if student.current_class else 'N/A',
            'current_class_id': student.current_class.id if student.current_class else None,
            'birth_date': student.birth_date.isoformat() if student.birth_date else None,
            'gender': student.gender,
            'phone': student.phone,
            'email': student.email,
        }
        
        return JsonResponse({'student': student_data})
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations de l'étudiant {student_id}: {e}")
        return JsonResponse({'error': 'Erreur lors de la récupération des informations'}, status=500)


# ==================== VUES POUR LES STRUCTURES DE FRAIS ====================

@login_required
def fee_structure_list(request):
    """
    Vue pour lister toutes les structures de frais avec filtres
    Optimisée avec select_related et prefetch_related
    """
    logger.info(f"Utilisateur {request.user} accède à la liste des structures de frais")
    
    search_form = FeeStructureSearchForm(request.GET)
    fee_structures = FeeStructure.objects.select_related(
        'school_class', 'school_class__level', 'year'
    ).prefetch_related(
        'tranches'
    ).all()
    
    if search_form.is_valid():
        year = search_form.cleaned_data.get('year')
        school_class = search_form.cleaned_data.get('school_class')
        
        if year:
            fee_structures = fee_structures.filter(year=year)
            logger.debug(f"Filtrage par année: {year}")
        
        if school_class:
            fee_structures = fee_structures.filter(school_class=school_class)
            logger.debug(f"Filtrage par classe: {school_class}")
    
    # Pagination
    paginator = Paginator(fee_structures, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Trouver l'année en cours
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_structures': fee_structures.count(),
        'current_year': current_year,
    }
    
    return render(request, 'finances/fee_structure_list.html', context)

@login_required
def fee_structure_create(request):
    """
    Vue pour créer une nouvelle structure de frais
    """
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    fee_structure = form.save(commit=False)
                    fee_structure.created_by = request.user
                    fee_structure.save()
                    
                    # Récupérer les données des tranches depuis le formulaire
                    tranches_data = request.POST.get('tranches_data')
                    if tranches_data:
                        try:
                            import json
                            tranches = json.loads(tranches_data)
                            
                            # Créer les tranches personnalisées
                            for tranche_data in tranches:
                                FeeTranche.objects.create(
                                    fee_structure=fee_structure,
                                    number=tranche_data['number'],
                                    amount=tranche_data['amount'],
                                    due_date=tranche_data['due_date']
                                )
                            
                            logger.info(f"Structure de frais créée avec {len(tranches)} tranches personnalisées par {request.user}: {fee_structure}")
                            messages.success(request, f"Structure de frais créée avec succès pour {fee_structure.school_class} - {fee_structure.year} ({len(tranches)} tranches)")
                            
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.error(f"Erreur lors du traitement des données des tranches: {e}")
                            # Fallback : créer des tranches automatiques
                            tranche_count = fee_structure.tranche_count
                            tuition_per_tranche = fee_structure.tuition_total / tranche_count
                            
                            for i in range(1, tranche_count + 1):
                                due_date = timezone.now().date() + timedelta(days=30 * i)
                                FeeTranche.objects.create(
                                    fee_structure=fee_structure,
                                    number=i,
                                    amount=tuition_per_tranche,
                                    due_date=due_date
                                )
                            
                            messages.warning(request, "Structure de frais créée avec des tranches automatiques (erreur dans les données personnalisées).")
                    else:
                        # Créer automatiquement les tranches si aucune donnée personnalisée
                        tranche_count = fee_structure.tranche_count
                        tuition_per_tranche = fee_structure.tuition_total / tranche_count
                        
                        for i in range(1, tranche_count + 1):
                            due_date = timezone.now().date() + timedelta(days=30 * i)
                            FeeTranche.objects.create(
                                fee_structure=fee_structure,
                                number=i,
                                amount=tuition_per_tranche,
                                due_date=due_date
                            )
                        
                        logger.info(f"Structure de frais créée avec {tranche_count} tranches automatiques par {request.user}: {fee_structure}")
                        messages.success(request, f"Structure de frais créée avec succès pour {fee_structure.school_class} - {fee_structure.year} ({tranche_count} tranches automatiques)")
                    
                    return redirect('finances:fee_structure_detail', pk=fee_structure.pk)
                    
            except Exception as e:
                logger.error(f"Erreur lors de la création de la structure de frais: {e}")
                messages.error(request, "Erreur lors de la création de la structure de frais.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de structure de frais: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FeeStructureForm()
    
    context = {
        'form': form,
        'title': 'Créer une structure de frais',
    }
    
    return render(request, 'finances/fee_structure_form.html', context)

@login_required
def fee_structure_update(request, pk):
    """
    Vue pour modifier une structure de frais existante
    """
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            try:
                with transaction.atomic():
                    fee_structure = form.save(commit=False)
                    fee_structure.updated_by = request.user
                    fee_structure.save()
                    
                    # Récupérer les données des tranches depuis le formulaire
                    tranches_data = request.POST.get('tranches_data')
                    if tranches_data:
                        try:
                            import json
                            new_tranches = json.loads(tranches_data)
                            
                            # Supprimer les anciennes tranches
                            fee_structure.tranches.all().delete()
                            
                            # Créer les nouvelles tranches
                            for tranche_data in new_tranches:
                                FeeTranche.objects.create(
                                    fee_structure=fee_structure,
                                    number=tranche_data['number'],
                                    amount=tranche_data['amount'],
                                    due_date=tranche_data['due_date']
                                )
                            
                            logger.info(f"Structure de frais modifiée avec {len(new_tranches)} tranches par {request.user}: {fee_structure}")
                            messages.success(request, f"Structure de frais modifiée avec succès ({len(new_tranches)} tranches mises à jour).")
                            
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.error(f"Erreur lors du traitement des données des tranches: {e}")
                            messages.error(request, "Erreur lors de la mise à jour des tranches. Les tranches existantes ont été conservées.")
                    
                    return redirect('finances:fee_structure_detail', pk=fee_structure.pk)
                    
            except Exception as e:
                logger.error(f"Erreur lors de la modification de la structure de frais: {e}")
                messages.error(request, "Erreur lors de la modification de la structure de frais.")
        else:
            logger.warning(f"Formulaire invalide lors de la modification de structure de frais: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FeeStructureForm(instance=fee_structure)
    
    # Récupérer les tranches existantes pour les afficher dans le formulaire
    existing_tranches = fee_structure.tranches.all().order_by('number')
    
    context = {
        'form': form,
        'fee_structure': fee_structure,
        'existing_tranches': existing_tranches,
        'title': 'Modifier la structure de frais',
    }
    
    return render(request, 'finances/fee_structure_form.html', context)

@login_required
def fee_structure_detail(request, pk):
    """
    Vue pour afficher les détails d'une structure de frais
    """
    fee_structure = get_object_or_404(FeeStructure.objects.select_related('school_class', 'year'), pk=pk)
    tranches = fee_structure.tranches.all()
    
    # Statistiques des paiements
    total_paid = TranchePayment.objects.filter(tranche__fee_structure=fee_structure).aggregate(
        total=Sum('amount'))['total'] or 0
    total_discounts = FeeDiscount.objects.filter(tranche__fee_structure=fee_structure).aggregate(
        total=Sum('amount'))['total'] or 0
    
    context = {
        'fee_structure': fee_structure,
        'tranches': tranches,
        'total_paid': total_paid,
        'total_discounts': total_discounts,
        'total_due': fee_structure.tuition_total,
        'total_remaining': fee_structure.tuition_total - total_paid - total_discounts,
    }
    
    logger.info(f"Utilisateur {request.user} consulte les détails de la structure de frais: {fee_structure}")
    
    return render(request, 'finances/fee_structure_detail.html', context)

@login_required
def fee_structure_delete(request, pk):
    """
    Vue pour supprimer une structure de frais
    """
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    
    if request.method == 'POST':
        try:
            # Vérifier s'il y a des paiements associés
            if TranchePayment.objects.filter(tranche__fee_structure=fee_structure).exists():
                messages.error(request, "Impossible de supprimer cette structure de frais car des paiements y sont associés.")
                return redirect('finances:fee_structure_detail', pk=pk)
            
            fee_structure.delete()
            logger.info(f"Structure de frais supprimée avec succès par {request.user}: {fee_structure}")
            messages.success(request, "Structure de frais supprimée avec succès.")
            return redirect('finances:fee_structure_list')
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la structure de frais: {e}")
            messages.error(request, "Erreur lors de la suppression de la structure de frais.")
    
    context = {
        'fee_structure': fee_structure,
    }
    
    return render(request, 'finances/fee_structure_confirm_delete.html', context)

# ==================== VUES POUR LES TRANCHES ====================

@login_required
def fee_tranche_create(request, fee_structure_pk):
    """
    Vue pour créer une nouvelle tranche pour une structure de frais
    """
    fee_structure = get_object_or_404(FeeStructure, pk=fee_structure_pk)
    
    if request.method == 'POST':
        form = FeeTrancheForm(request.POST)
        if form.is_valid():
            try:
                tranche = form.save(commit=False)
                tranche.fee_structure = fee_structure
                tranche.save()
                
                logger.info(f"Tranche créée avec succès par {request.user}: {tranche}")
                messages.success(request, f"Tranche {tranche.number} créée avec succès.")
                return redirect('finances:fee_structure_detail', pk=fee_structure_pk)
                
            except Exception as e:
                logger.error(f"Erreur lors de la création de la tranche: {e}")
                messages.error(request, "Erreur lors de la création de la tranche.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de tranche: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FeeTrancheForm()
    
    context = {
        'form': form,
        'fee_structure': fee_structure,
        'title': 'Créer une tranche',
    }
    
    return render(request, 'finances/fee_tranche_form.html', context)

@login_required
def fee_tranche_update(request, pk):
    """
    Vue pour modifier une tranche existante
    """
    tranche = get_object_or_404(FeeTranche, pk=pk)
    
    if request.method == 'POST':
        form = FeeTrancheForm(request.POST, instance=tranche)
        if form.is_valid():
            try:
                tranche = form.save()
                
                logger.info(f"Tranche modifiée avec succès par {request.user}: {tranche}")
                messages.success(request, f"Tranche {tranche.number} modifiée avec succès.")
                return redirect('finances:fee_structure_detail', pk=tranche.fee_structure.pk)
                
            except Exception as e:
                logger.error(f"Erreur lors de la modification de la tranche: {e}")
                messages.error(request, "Erreur lors de la modification de la tranche.")
        else:
            logger.warning(f"Formulaire invalide lors de la modification de tranche: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FeeTrancheForm(instance=tranche)
    
    context = {
        'form': form,
        'tranche': tranche,
        'title': 'Modifier la tranche',
    }
    
    return render(request, 'finances/fee_tranche_form.html', context)

@login_required
def fee_tranche_delete(request, pk):
    """
    Vue pour supprimer une tranche
    """
    tranche = get_object_or_404(FeeTranche, pk=pk)
    
    if request.method == 'POST':
        try:
            # Vérifier s'il y a des paiements associés
            if TranchePayment.objects.filter(tranche=tranche).exists():
                messages.error(request, "Impossible de supprimer cette tranche car des paiements y sont associés.")
                return redirect('finances:fee_structure_detail', pk=tranche.fee_structure.pk)
            
            tranche.delete()
            logger.info(f"Tranche supprimée avec succès par {request.user}: {tranche}")
            messages.success(request, f"Tranche {tranche.number} supprimée avec succès.")
            return redirect('finances:fee_structure_detail', pk=tranche.fee_structure.pk)
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la tranche: {e}")
            messages.error(request, "Erreur lors de la suppression de la tranche.")
    
    context = {
        'tranche': tranche,
    }
    
    return render(request, 'finances/fee_tranche_confirm_delete.html', context)

# ==================== VUES POUR LES PAIEMENTS ====================

@login_required
def payment_list(request):
    """
    Vue pour lister tous les paiements avec filtres
    Optimisée avec select_related et prefetch_related
    """
    logger.info(f"Utilisateur {request.user} accède à la liste des paiements")
    
    search_form = PaymentSearchForm(request.GET)
    
    # Récupérer les paiements de tranches
    tranche_payments = TranchePayment.objects.select_related(
        'student', 'student__current_class', 'student__current_class__level',
        'tranche', 'tranche__fee_structure', 'tranche__fee_structure__year',
        'created_by'
    ).all()
    
    # Récupérer les paiements d'inscription
    inscription_payments = InscriptionPayment.objects.select_related(
        'student', 'student__current_class', 'student__current_class__level',
        'fee_structure', 'fee_structure__year', 'created_by'
    ).all()
    
    if search_form.is_valid():
        student_name = search_form.cleaned_data.get('student_name')
        school_class = search_form.cleaned_data.get('school_class')
        student = search_form.cleaned_data.get('student')
        payment_type = search_form.cleaned_data.get('payment_type')
        tranche = search_form.cleaned_data.get('tranche')
        mode = search_form.cleaned_data.get('mode')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')
        
        # Filtrage par nom d'étudiant
        if student_name:
            tranche_payments = tranche_payments.filter(
                Q(student__first_name__icontains=student_name) |
                Q(student__last_name__icontains=student_name) |
                Q(student__matricule__icontains=student_name)
            )
            inscription_payments = inscription_payments.filter(
                Q(student__first_name__icontains=student_name) |
                Q(student__last_name__icontains=student_name) |
                Q(student__matricule__icontains=student_name)
            )
        
        # Filtrage par classe
        if school_class:
            tranche_payments = tranche_payments.filter(student__current_class=school_class)
            inscription_payments = inscription_payments.filter(student__current_class=school_class)
        
        # Filtrage par étudiant spécifique
        if student:
            tranche_payments = tranche_payments.filter(student=student)
            inscription_payments = inscription_payments.filter(student=student)
        
        # Filtrage par type de paiement
        if payment_type == 'inscription':
            tranche_payments = TranchePayment.objects.none()
        elif payment_type == 'tranche':
            inscription_payments = InscriptionPayment.objects.none()
        
        # Filtrage par tranche (uniquement pour les paiements de tranches)
        if tranche:
            tranche_payments = tranche_payments.filter(tranche=tranche)
        
        # Filtrage par mode de paiement
        if mode:
            tranche_payments = tranche_payments.filter(mode=mode)
            inscription_payments = inscription_payments.filter(mode=mode)
        
        # Filtrage par date
        if date_from:
            tranche_payments = tranche_payments.filter(payment_date__gte=date_from)
            inscription_payments = inscription_payments.filter(payment_date__gte=date_from)
        if date_to:
            tranche_payments = tranche_payments.filter(payment_date__lte=date_to)
            inscription_payments = inscription_payments.filter(payment_date__lte=date_to)
    
    # Combiner les paiements avec un indicateur de type
    all_payments = []
    
    for payment in tranche_payments:
        payment.payment_type = 'tranche'
        all_payments.append(payment)
    
    for payment in inscription_payments:
        payment.payment_type = 'inscription'
        all_payments.append(payment)
    
    # Trier par date de création (plus récent en premier)
    all_payments.sort(key=lambda x: x.created_at, reverse=True)
    
    # Pagination
    paginator = Paginator(all_payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_tranche_payments = tranche_payments.count()
    total_inscription_payments = inscription_payments.count()
    total_tranche_amount = tranche_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_inscription_amount = inscription_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_tranche_payments': total_tranche_payments,
        'total_inscription_payments': total_inscription_payments,
        'total_tranche_amount': total_tranche_amount,
        'total_inscription_amount': total_inscription_amount,
        'total_payments': total_tranche_payments + total_inscription_payments,
        'total_amount': total_tranche_amount + total_inscription_amount,
    }
    
    return render(request, 'finances/payment_list.html', context)

@login_required
def payment_create(request):
    """
    Vue pour créer un nouveau paiement
    """
    if request.method == 'POST':
        form = TranchePaymentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                payment = form.save(commit=False)
                payment.created_by = request.user
                
                # Générer un numéro de reçu automatique si non fourni
                if not payment.receipt:
                    payment.receipt = f"REC-{timezone.now().strftime('%Y%m%d')}-{TranchePayment.objects.count() + 1:04d}"
                
                payment.save()
                
                # Envoyer les notifications après la création du paiement
                try:
                    from notifications.services import notification_service
                    
                    # Préparer les données pour la notification
                    payment_data = {
                        'student_name': f"{payment.student.first_name} {payment.student.last_name}",
                        'tranche_number': payment.tranche.number,
                        'class_name': payment.tranche.fee_structure.school_class.name,
                        'school_year': payment.tranche.fee_structure.year.annee,
                        'amount': payment.amount,
                        'payment_mode': payment.get_mode_display(),
                        'receipt_number': payment.receipt,
                        'payment_date': payment.payment_date.strftime('%d/%m/%Y'),
                        'guardian_email': payment.student.guardians.first().email if payment.student.guardians.exists() else None,
                        'guardian_phone': payment.student.guardians.first().phone if payment.student.guardians.exists() else None,
                        'school_phone': getattr(payment.tranche.fee_structure.school_class.school, 'phone', None),
                        'school_email': getattr(payment.tranche.fee_structure.school_class.school, 'email', None),
                    }
                    
                    # Envoyer les notifications
                    notification_results = notification_service.send_payment_notification(payment_data)
                    
                    if notification_results['email_sent'] or notification_results['sms_sent']:
                        logger.info(f"Notifications envoyées pour le paiement {payment.pk}: {notification_results}")
                        if notification_results['email_sent']:
                            messages.success(request, "Notification par email envoyée au tuteur.")
                        if notification_results['sms_sent']:
                            messages.success(request, "Notification par SMS envoyée au tuteur.")
                    else:
                        logger.warning(f"Échec de l'envoi des notifications pour le paiement {payment.pk}: {notification_results['errors']}")
                        messages.warning(request, "Paiement enregistré mais échec de l'envoi des notifications.")
                        
                except ImportError:
                    logger.warning("Service de notification non disponible")
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi des notifications: {e}")
                    messages.warning(request, "Paiement enregistré mais échec de l'envoi des notifications.")
                
                logger.info(f"Paiement créé avec succès par {request.user}: {payment}")
                messages.success(request, f"Paiement de {payment.amount} FCFA enregistré avec succès.")
                return redirect('finances:payment_detail', pk=payment.pk)
                
            except Exception as e:
                logger.error(f"Erreur lors de la création du paiement: {e}")
                messages.error(request, "Erreur lors de l'enregistrement du paiement.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de paiement: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = TranchePaymentForm()
    
    context = {
        'form': form,
        'title': 'Enregistrer un paiement',
    }
    
    return render(request, 'finances/payment_form.html', context)

@login_required
def inscription_payment_create(request):
    """
    Vue pour créer un nouveau paiement de frais d'inscription
    """
    if request.method == 'POST':
        form = InscriptionPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                payment = form.save(commit=False)
                payment.created_by = request.user
                
                # Générer un numéro de reçu automatique si non fourni
                if not payment.receipt:
                    payment.receipt = f"INS-{timezone.now().strftime('%Y%m%d')}-{InscriptionPayment.objects.count() + 1:04d}"
                
                payment.save()
                
                # Envoyer les notifications après la création du paiement d'inscription
                try:
                    from notifications.services import notification_service
                    
                    # Préparer les données pour la notification
                    inscription_data = {
                        'student_name': f"{payment.student.first_name} {payment.student.last_name}",
                        'class_name': payment.fee_structure.school_class.name,
                        'school_year': payment.fee_structure.year.annee,
                        'amount': payment.amount,
                        'payment_mode': payment.get_mode_display(),
                        'receipt_number': payment.receipt,
                        'payment_date': payment.payment_date.strftime('%d/%m/%Y'),
                        'guardian_email': payment.student.guardians.first().email if payment.student.guardians.exists() else None,
                        'guardian_phone': payment.student.guardians.first().phone if payment.student.guardians.exists() else None,
                        'school_phone': getattr(payment.fee_structure.school_class.school, 'phone', None),
                        'school_email': getattr(payment.fee_structure.school_class.school, 'email', None),
                    }
                    
                    # Envoyer les notifications
                    notification_results = notification_service.send_inscription_notification(inscription_data)
                    
                    if notification_results['email_sent'] or notification_results['sms_sent']:
                        logger.info(f"Notifications d'inscription envoyées pour le paiement {payment.pk}: {notification_results}")
                        if notification_results['email_sent']:
                            messages.success(request, "Notification par email envoyée au tuteur.")
                        if notification_results['sms_sent']:
                            messages.success(request, "Notification par SMS envoyée au tuteur.")
                    else:
                        logger.warning(f"Échec de l'envoi des notifications d'inscription pour le paiement {payment.pk}: {notification_results['errors']}")
                        messages.warning(request, "Paiement d'inscription enregistré mais échec de l'envoi des notifications.")
                        
                except ImportError:
                    logger.warning("Service de notification non disponible")
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi des notifications d'inscription: {e}")
                    messages.warning(request, "Paiement d'inscription enregistré mais échec de l'envoi des notifications.")
                
                logger.info(f"Paiement d'inscription créé avec succès par {request.user}: {payment}")
                messages.success(request, f"Paiement d'inscription de {payment.amount} FCFA enregistré avec succès.")
                return redirect('finances:payment_list')
                
            except Exception as e:
                logger.error(f"Erreur lors de la création du paiement d'inscription: {e}")
                messages.error(request, "Erreur lors de l'enregistrement du paiement d'inscription.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de paiement d'inscription: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = InscriptionPaymentForm()
    
    context = {
        'form': form,
        'title': 'Enregistrer un paiement d\'inscription',
    }
    
    return render(request, 'finances/inscription_payment_form.html', context)

@login_required
def payment_detail(request, pk, payment_type=None):
    """
    Vue pour afficher les détails d'un paiement (tranche ou inscription)
    Si payment_type est fourni dans l'URL, on force le lookup dans le modèle correspondant
    pour éviter toute ambiguïté d'ID.
    """
    payment = None
    resolved_type = None

    if payment_type in {"tranche", "inscription"}:
        if payment_type == 'tranche':
            payment = get_object_or_404(
                TranchePayment.objects.select_related('student', 'tranche', 'tranche__fee_structure', 'created_by'),
                pk=pk
            )
            resolved_type = 'tranche'
        else:
            payment = get_object_or_404(
                InscriptionPayment.objects.select_related('student', 'fee_structure', 'created_by'),
                pk=pk
            )
            resolved_type = 'inscription'
    else:
        # rétro-compatibilité: tenter de résoudre automatiquement
        try:
            payment = TranchePayment.objects.select_related(
                'student', 'tranche', 'tranche__fee_structure', 'created_by'
            ).get(pk=pk)
            resolved_type = 'tranche'
        except TranchePayment.DoesNotExist:
            try:
                payment = InscriptionPayment.objects.select_related(
                    'student', 'fee_structure', 'created_by'
                ).get(pk=pk)
                resolved_type = 'inscription'
            except InscriptionPayment.DoesNotExist:
                raise Http404("Paiement non trouvé")

    context = {
        'payment': payment,
        'payment_type': resolved_type,
    }

    logger.info(f"Utilisateur {request.user} consulte les détails du paiement: {payment}")

    return render(request, 'finances/payment_detail.html', context)

@login_required
def payment_receipt_pdf(request, pk, payment_type=None):
    """
    Vue pour générer un PDF du reçu de paiement
    """
    # Résoudre explicitement si payment_type précisé
    if payment_type in {"tranche", "inscription"}:
        if payment_type == 'tranche':
            payment = get_object_or_404(
                TranchePayment.objects.select_related('student', 'tranche', 'tranche__fee_structure', 'created_by'),
                pk=pk
            )
        else:
            payment = get_object_or_404(
                InscriptionPayment.objects.select_related('student', 'fee_structure', 'created_by'),
                pk=pk
            )
    else:
        # fallback rétro-compatibilité
        try:
            payment = TranchePayment.objects.select_related(
                'student', 'tranche', 'tranche__fee_structure', 'created_by'
            ).get(pk=pk)
            payment_type = 'tranche'
        except TranchePayment.DoesNotExist:
            try:
                payment = InscriptionPayment.objects.select_related(
                    'student', 'fee_structure', 'created_by'
                ).get(pk=pk)
                payment_type = 'inscription'
            except InscriptionPayment.DoesNotExist:
                raise Http404("Paiement non trouvé")
    
    # Préparer les chemins des images
    school = payment.student.school
    logo_url = None
    signature_url = None
    
    # Récupérer l'en-tête de document de l'école
    document_header = school.get_active_header()
    
    if document_header and document_header.logo:
        try:
            logo_url = request.build_absolute_uri(document_header.logo.url)
        except Exception:
            logo_url = None
    
    if document_header and document_header.signature:
        try:
            signature_url = request.build_absolute_uri(document_header.signature.url)
        except Exception:
            signature_url = None
    
    # Fallback: logo statique explicite si pas de logo école
    if not logo_url:
        logo_url = request.build_absolute_uri(static('images/logo.png'))
    
    # Générer un QR-code (data URI) avec les infos essentielles
    qr_data_url = None
    try:
        import qrcode  # type: ignore
        from io import BytesIO
        import base64

        payload = {
            'id': payment.pk,
            'type': payment_type or ('tranche' if isinstance(payment, TranchePayment) else 'inscription'),
            'receipt': str(payment.receipt),
            'student_id': payment.student_id,
            'student': f"{payment.student.last_name} {payment.student.first_name}",
            'amount': float(payment.amount),
            'date': payment.payment_date.strftime('%Y-%m-%d'),
            'school': getattr(payment.student.school, 'nom', None),
        }

        qr = qrcode.QRCode(version=None, box_size=3, border=1)
        import json as _json
        qr.add_data(_json.dumps(payload, ensure_ascii=False))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode('ascii')
    except Exception:
        qr_data_url = None

    context = {
        'payment': payment,
        'payment_type': payment_type or ('tranche' if isinstance(payment, TranchePayment) else 'inscription'),
        'school': school,
        'document_header': school.get_active_header() if school else None,
        'logo_url': logo_url,
        'signature_url': signature_url,
        'qr_data_url': qr_data_url,
    }
    
    # Rendre le template HTML
    html_string = render_to_string('finances/payment_receipt_pdf.html', context)
    
    # Configuration des polices
    font_config = FontConfiguration()
    
    # Créer le PDF avec WeasyPrint
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf(
        stylesheets=[],
        font_config=font_config
    )
    
    # Créer la réponse HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="recu_paiement_{payment.receipt}.pdf"'
    
    logger.info(f"PDF du reçu généré pour le paiement {payment} par {request.user}")
    
    return response

@login_required
def payment_receipt(request, pk, payment_type=None):
    """
    Vue pour générer et afficher un reçu de paiement (tranche ou inscription)
    """
    # Résoudre explicitement si payment_type précisé
    if payment_type in {"tranche", "inscription"}:
        if payment_type == 'tranche':
            payment = get_object_or_404(
                TranchePayment.objects.select_related('student', 'tranche', 'tranche__fee_structure', 'created_by'),
                pk=pk
            )
        else:
            payment = get_object_or_404(
                InscriptionPayment.objects.select_related('student', 'fee_structure', 'created_by'),
                pk=pk
            )
    else:
        # fallback rétro-compatibilité
        try:
            payment = TranchePayment.objects.select_related(
                'student', 'tranche', 'tranche__fee_structure', 'created_by'
            ).get(pk=pk)
            payment_type = 'tranche'
        except TranchePayment.DoesNotExist:
            try:
                payment = InscriptionPayment.objects.select_related(
                    'student', 'fee_structure', 'created_by'
                ).get(pk=pk)
                payment_type = 'inscription'
            except InscriptionPayment.DoesNotExist:
                raise Http404("Paiement non trouvé")
    
    context = {
        'payment': payment,
        'payment_type': payment_type or ('tranche' if isinstance(payment, TranchePayment) else 'inscription'),
        'school': payment.student.school,
    }
    
    logger.info(f"Reçu généré pour le paiement {payment} par {request.user}")
    
    return render(request, 'finances/payment_receipt.html', context)

@login_required
def bulk_payment_create(request):
    """
    Vue pour créer des paiements en lot
    """
    if request.method == 'POST':
        form = BulkTranchePaymentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    school_class = form.cleaned_data['school_class']
                    tranche = form.cleaned_data['tranche']
                    mode = form.cleaned_data['mode']
                    receipt_prefix = form.cleaned_data.get('receipt_prefix', 'REC')
                    
                    # Récupérer tous les étudiants de la classe
                    students = Student.objects.filter(current_class=school_class, is_active=True)
                    
                    payments_created = 0
                    for student in students:
                        # Vérifier si l'étudiant a déjà payé cette tranche
                        if not TranchePayment.objects.filter(student=student, tranche=tranche).exists():
                            receipt_number = f"{receipt_prefix}-{timezone.now().strftime('%Y%m%d')}-{payments_created + 1:04d}"
                            
                            TranchePayment.objects.create(
                                student=student,
                                tranche=tranche,
                                amount=tranche.amount,
                                mode=mode,
                                receipt=receipt_number,
                                created_by=request.user
                            )
                            payments_created += 1
                    
                    logger.info(f"Paiements en lot créés avec succès par {request.user}: {payments_created} paiements")
                    messages.success(request, f"{payments_created} paiements créés avec succès.")
                    return redirect('finances:payment_list')
                    
            except Exception as e:
                logger.error(f"Erreur lors de la création des paiements en lot: {e}")
                messages.error(request, "Erreur lors de la création des paiements en lot.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de paiements en lot: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = BulkTranchePaymentForm()
    
    context = {
        'form': form,
        'title': 'Créer des paiements en lot',
    }
    
    return render(request, 'finances/bulk_payment_form.html', context)

# ==================== VUES POUR LES REMISES/BOURSES ====================

@login_required
def discount_list(request):
    """
    Vue pour lister toutes les remises/bourses
    Optimisée avec select_related
    """
    discounts = FeeDiscount.objects.select_related(
        'student', 'student__current_class', 'tranche', 'tranche__fee_structure', 'created_by'
    ).all()
    
    # Pagination
    paginator = Paginator(discounts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques - optimisées
    stats = discounts.aggregate(
        total_count=Count('id'),
        total_amount=Sum('amount')
    )
    
    context = {
        'page_obj': page_obj,
        'total_discounts': stats['total_count'] or 0,
        'total_amount': stats['total_amount'] or 0,
    }
    
    logger.info(f"Utilisateur {request.user} accède à la liste des remises")
    
    return render(request, 'finances/discount_list.html', context)

@login_required
def discount_create(request):
    """
    Vue pour créer une nouvelle remise/bourse
    """
    if request.method == 'POST':
        form = FeeDiscountForm(request.POST)
        if form.is_valid():
            try:
                discount = form.save(commit=False)
                discount.created_by = request.user
                discount.save()
                
                logger.info(f"Remise créée avec succès par {request.user}: {discount}")
                messages.success(request, f"Remise de {discount.amount} FCFA accordée avec succès.")
                return redirect('finances:discount_list')
                
            except Exception as e:
                logger.error(f"Erreur lors de la création de la remise: {e}")
                messages.error(request, "Erreur lors de l'attribution de la remise.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de remise: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FeeDiscountForm()
    
    context = {
        'form': form,
        'title': 'Accorder une remise',
    }
    
    return render(request, 'finances/discount_form.html', context)

@login_required
def discount_update(request, pk):
    """
    Vue pour modifier une remise existante
    """
    discount = get_object_or_404(FeeDiscount, pk=pk)
    
    if request.method == 'POST':
        form = FeeDiscountForm(request.POST, instance=discount)
        if form.is_valid():
            try:
                discount = form.save()
                
                logger.info(f"Remise modifiée avec succès par {request.user}: {discount}")
                messages.success(request, "Remise modifiée avec succès.")
                return redirect('finances:discount_list')
                
            except Exception as e:
                logger.error(f"Erreur lors de la modification de la remise: {e}")
                messages.error(request, "Erreur lors de la modification de la remise.")
        else:
            logger.warning(f"Formulaire invalide lors de la modification de remise: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FeeDiscountForm(instance=discount)
    
    context = {
        'form': form,
        'discount': discount,
        'title': 'Modifier la remise',
    }
    
    return render(request, 'finances/discount_form.html', context)

@login_required
def discount_delete(request, pk):
    """
    Vue pour supprimer une remise
    """
    discount = get_object_or_404(FeeDiscount, pk=pk)
    
    if request.method == 'POST':
        try:
            discount.delete()
            logger.info(f"Remise supprimée avec succès par {request.user}: {discount}")
            messages.success(request, "Remise supprimée avec succès.")
            return redirect('finances:discount_list')
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la remise: {e}")
            messages.error(request, "Erreur lors de la suppression de la remise.")
    
    context = {
        'discount': discount,
    }
    
    return render(request, 'finances/discount_confirm_delete.html', context)

# ==================== VUES POUR LES MORATOIRES ====================

@login_required
def moratorium_list(request):
    """
    Vue pour lister tous les moratoires
    Optimisée avec select_related
    """
    moratoriums = Moratorium.objects.select_related(
        'student', 'student__current_class', 'tranche', 'tranche__fee_structure'
    ).order_by('-requested_at')
    
    # Pagination
    paginator = Paginator(moratoriums, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques - optimisées
    stats = moratoriums.aggregate(
        total_count=Count('id'),
        pending_count=Count('id', filter=Q(is_approved=False))
    )
    
    context = {
        'page_obj': page_obj,
        'total_moratoriums': stats['total_count'] or 0,
        'pending_moratoriums': stats['pending_count'] or 0,
    }
    
    logger.info(f"Utilisateur {request.user} accède à la liste des moratoires")
    
    return render(request, 'finances/moratorium_list.html', context)

@login_required
def moratorium_create(request):
    """
    Vue pour créer une nouvelle demande de moratoire
    """
    if request.method == 'POST':
        form = MoratoriumForm(request.POST)
        if form.is_valid():
            try:
                moratorium = form.save(commit=False)
                moratorium.save()
                
                logger.info(f"Demande de moratoire créée avec succès par {request.user}: {moratorium}")
                messages.success(request, "Demande de moratoire soumise avec succès.")
                return redirect('finances:moratorium_list')
                
            except Exception as e:
                logger.error(f"Erreur lors de la création du moratoire: {e}")
                messages.error(request, "Erreur lors de la soumission de la demande de moratoire.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de moratoire: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = MoratoriumForm()
    
    context = {
        'form': form,
        'title': 'Demander un moratoire',
    }
    
    return render(request, 'finances/moratorium_form.html', context)

@login_required
def moratorium_approve(request, pk):
    """
    Vue pour approuver un moratoire
    """
    moratorium = get_object_or_404(Moratorium, pk=pk)
    
    if request.method == 'POST':
        try:
            moratorium.is_approved = True
            moratorium.approved_at = timezone.now()
            moratorium.approved_by = request.user
            moratorium.save()
            
            logger.info(f"Moratoire approuvé avec succès par {request.user}: {moratorium}")
            messages.success(request, "Moratoire approuvé avec succès.")
            return redirect('finances:moratorium_approved', pk=moratorium.pk)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'approbation du moratoire: {e}")
            messages.error(request, "Erreur lors de l'approbation du moratoire.")
    
    context = {
        'moratorium': moratorium,
    }
    
    return render(request, 'finances/moratorium_approve.html', context)

@login_required
def moratorium_approved(request, pk):
    """
    Vue pour afficher le moratoire approuvé avec option d'impression
    """
    moratorium = get_object_or_404(Moratorium, pk=pk)
    
    if not moratorium.is_approved:
        messages.error(request, "Ce moratoire n'est pas encore approuvé.")
        return redirect('finances:moratorium_list')
    
    context = {
        'moratorium': moratorium,
    }
    
    return render(request, 'finances/moratorium_approved.html', context)

@login_required
def moratorium_pdf(request, pk):
    """
    Vue pour générer le PDF du moratoire approuvé
    """
    moratorium = get_object_or_404(Moratorium, pk=pk)
    
    if not moratorium.is_approved:
        messages.error(request, "Ce moratoire n'est pas encore approuvé.")
        return redirect('finances:moratorium_list')
    
    # Récupérer les informations de l'école
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les informations de l'établissement
    try:
        from school.models import School
        school = School.objects.first()
        
        # Récupérer l'en-tête de document de l'école
        document_header = school.get_active_header() if school else None
        
        # Construire les URLs absolues pour les images
        school_logo_url = None
        school_signature_url = None
        if document_header:
            if document_header.logo:
                try:
                    school_logo_url = request.build_absolute_uri(document_header.logo.url)
                except Exception:
                    school_logo_url = None
            
            if document_header.signature:
                try:
                    school_signature_url = request.build_absolute_uri(document_header.signature.url)
                except Exception:
                    school_signature_url = None
    except:
        school = None
        document_header = None
        school_logo_url = None
        school_signature_url = None
    
    context = {
        'moratorium': moratorium,
        'current_year': current_year,
        'school': school,
        'document_header': document_header,
        'school_logo': school_logo_url,
        'school_signature': school_signature_url,
    }
    
    # Générer le PDF
    html_string = render_to_string('finances/moratorium_pdf.html', context)
    
    # Créer le PDF
    pdf = HTML(string=html_string).write_pdf()
    
    # Créer la réponse HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="moratoire_{moratorium.student.last_name}_{moratorium.student.first_name}_{moratorium.tranche.number}.pdf"'
    
    return response

@login_required
def moratorium_delete(request, pk):
    """
    Vue pour supprimer un moratoire
    """
    moratorium = get_object_or_404(Moratorium, pk=pk)
    
    if request.method == 'POST':
        try:
            moratorium.delete()
            logger.info(f"Moratoire supprimé avec succès par {request.user}: {moratorium}")
            messages.success(request, "Moratoire supprimé avec succès.")
            return redirect('finances:moratorium_list')
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du moratoire: {e}")
            messages.error(request, "Erreur lors de la suppression du moratoire.")
    
    context = {
        'moratorium': moratorium,
    }
    
    return render(request, 'finances/moratorium_confirm_delete.html', context)

# ==================== VUES POUR LES REMBOURSEMENTS ====================

@login_required
def refund_list(request):
    """
    Vue pour lister tous les remboursements
    Optimisée avec select_related
    """
    refunds = PaymentRefund.objects.select_related(
        'payment', 'payment__student', 'payment__tranche', 'created_by'
    ).all()
    
    # Pagination
    paginator = Paginator(refunds, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques - optimisées
    stats = refunds.aggregate(
        total_count=Count('id'),
        total_amount=Sum('amount')
    )
    
    context = {
        'page_obj': page_obj,
        'total_refunds': stats['total_count'] or 0,
        'total_amount': stats['total_amount'] or 0,
    }
    
    logger.info(f"Utilisateur {request.user} accède à la liste des remboursements")
    
    return render(request, 'finances/refund_list.html', context)

@login_required
def refund_create(request):
    """
    Vue pour créer un nouveau remboursement
    """
    if request.method == 'POST':
        form = PaymentRefundForm(request.POST)
        if form.is_valid():
            try:
                refund = form.save(commit=False)
                refund.created_by = request.user
                refund.save()
                
                logger.info(f"Remboursement créé avec succès par {request.user}: {refund}")
                messages.success(request, f"Remboursement de {refund.amount} FCFA effectué avec succès.")
                return redirect('finances:refund_list')
                
            except Exception as e:
                logger.error(f"Erreur lors de la création du remboursement: {e}")
                messages.error(request, "Erreur lors de l'effectuation du remboursement.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de remboursement: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = PaymentRefundForm()
    
    context = {
        'form': form,
        'title': 'Effectuer un remboursement',
    }
    
    return render(request, 'finances/refund_form.html', context)

# ==================== VUES POUR LES FRAIS ANNEXES ====================

@login_required
def extra_fee_list(request):
    """
    Vue pour lister tous les frais annexes
    Optimisée avec select_related
    """
    extra_fees = ExtraFee.objects.select_related(
        'fee_type', 'year'
    ).prefetch_related('classes').order_by('-created_at')
    
    # Filtres
    search = request.GET.get('search', '')
    fee_type = request.GET.get('fee_type', '')
    year = request.GET.get('year', '')
    
    if search:
        extra_fees = extra_fees.filter(Q(name__icontains=search) | Q(description__icontains=search))
    
    if fee_type:
        extra_fees = extra_fees.filter(fee_type_id=fee_type)
    
    if year:
        extra_fees = extra_fees.filter(year_id=year)
    
    # Pagination
    paginator = Paginator(extra_fees, 20)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    
    # Calculer les statistiques
    total_extra_fees = extra_fees.count()
    total_amount = sum(fee.amount for fee in extra_fees)
    
    context = {
        'page_obj': page_obj,
        'total_extra_fees': total_extra_fees,
        'total_amount': total_amount,
        'fee_types': ExtraFeeType.objects.filter(is_active=True),
        'years': SchoolYear.objects.all().order_by('-annee'),
        'search': search,
        'selected_fee_type': fee_type,
        'selected_year': year
    }
    
    return render(request, 'finances/extra_fee_list.html', context)

@login_required
def extra_fee_create(request):
    """
    Vue pour créer un nouveau frais annexe
    """
    if request.method == 'POST':
        form = ExtraFeeForm(request.POST)
        if form.is_valid():
            try:
                extra_fee = form.save(commit=False)
                extra_fee.created_by = request.user
                extra_fee.save()
                form.save_m2m()  # Pour les relations many-to-many
                messages.success(request, 'Frais annexe créé avec succès.')
                return redirect('finances:extra_fee_list')
            except Exception as e:
                logger.error(f"Erreur lors de la création du frais annexe: {e}")
                messages.error(request, "Erreur lors de la création du frais annexe.")
        else:
            logger.warning(f"Formulaire invalide lors de la création de frais annexe: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = ExtraFeeForm()
    
    return render(request, 'finances/extra_fee_form.html', {'form': form, 'title': 'Créer un frais annexe'})

@login_required
def extra_fee_update(request, pk):
    """
    Vue pour modifier un frais annexe existant
    """
    extra_fee = get_object_or_404(ExtraFee, pk=pk)
    
    if request.method == 'POST':
        form = ExtraFeeForm(request.POST, instance=extra_fee)
        if form.is_valid():
            try:
                extra_fee = form.save(commit=False)
                extra_fee.save()
                form.save_m2m()
                messages.success(request, 'Frais annexe modifié avec succès.')
                return redirect('finances:extra_fee_list')
            except Exception as e:
                logger.error(f"Erreur lors de la modification du frais annexe: {e}")
                messages.error(request, "Erreur lors de la modification du frais annexe.")
        else:
            logger.warning(f"Formulaire invalide lors de la modification de frais annexe: {form.errors}")
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = ExtraFeeForm(instance=extra_fee)
    
    return render(request, 'finances/extra_fee_form.html', {'form': form, 'title': 'Modifier le frais annexe'})

@login_required
def extra_fee_delete(request, pk):
    """
    Vue pour supprimer un frais annexe
    """
    extra_fee = get_object_or_404(ExtraFee, pk=pk)
    
    if request.method == 'POST':
        try:
            extra_fee.delete()
            messages.success(request, 'Frais annexe supprimé avec succès.')
            return redirect('finances:extra_fee_list')
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du frais annexe: {e}")
            messages.error(request, "Erreur lors de la suppression du frais annexe.")
    
    return render(request, 'finances/extra_fee_confirm_delete.html', {'fee': extra_fee})

@login_required
def extra_fee_detail(request, pk):
    """
    Vue pour afficher les détails d'un frais annexe
    """
    extra_fee = get_object_or_404(ExtraFee.objects.select_related('fee_type', 'year').prefetch_related('classes'), pk=pk)
    
    # Statistiques des paiements
    payments = extra_fee.payments.all()
    total_paid = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_students = extra_fee.get_concerned_students().count()
    paid_students = payments.count()
    
    context = {
        'extra_fee': extra_fee,
        'payments': payments,
        'total_paid': total_paid,
        'total_students': total_students,
        'paid_students': paid_students,
        'unpaid_students': total_students - paid_students
    }
    
    return render(request, 'finances/extra_fee_detail.html', context)

# ===== PAIEMENTS DES FRAIS ANNEXES =====

@login_required
def extra_fee_payment_create(request):
    """
    Vue pour créer un nouveau paiement de frais annexe
    """
    if request.method == 'POST':
        form = ExtraFeePaymentForm(request.POST)
        if form.is_valid():
            # Créer le paiement sans le champ school_class qui n'existe pas dans le modèle
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.save()
            messages.success(request, 'Paiement enregistré avec succès.')
            return redirect('finances:extra_fee_payment_list')
        else:
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        form = ExtraFeePaymentForm()
    
    return render(request, 'finances/extra_fee_payment_form.html', {'form': form, 'title': 'Enregistrer un paiement'})

@login_required
def extra_fee_payment_list(request):
    """
    Vue pour lister tous les paiements de frais annexes
    """
    # Récupérer tous les paiements pour les statistiques
    all_payments = ExtraFeePayment.objects.select_related('student', 'extra_fee', 'student__current_class')
    
    # Filtres
    search = request.GET.get('search', '')
    extra_fee = request.GET.get('extra_fee', '')
    school_class = request.GET.get('school_class', '')
    mode = request.GET.get('mode', '')
    
    payments = all_payments
    
    if search:
        payments = payments.filter(
            Q(student__first_name__icontains=search) | 
            Q(student__last_name__icontains=search) |
            Q(extra_fee__name__icontains=search) |
            Q(receipt__icontains=search)
        )
    
    if extra_fee:
        payments = payments.filter(extra_fee_id=extra_fee)
    
    if school_class:
        payments = payments.filter(student__current_class_id=school_class)
    
    if mode:
        payments = payments.filter(mode=mode)
    
    # Statistiques
    total_payments = all_payments.count()
    total_amount = all_payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Paiements du mois en cours
    from django.utils import timezone
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_payments = all_payments.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).count()
    monthly_amount = all_payments.filter(
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Pagination
    paginator = Paginator(payments.order_by('-created_at'), 20)
    page = request.GET.get('page')
    payments = paginator.get_page(page)
    
    context = {
        'payments': payments,
        'extra_fee_payments': payments,  # Pour la compatibilité avec le template
        'total_payments': total_payments,
        'total_amount': total_amount,
        'monthly_payments': monthly_payments,
        'monthly_amount': monthly_amount,
        'extra_fees': ExtraFee.objects.filter(is_active=True),
        'school_classes': SchoolClass.objects.all(),
        'search': search,
        'selected_extra_fee': extra_fee,
        'selected_school_class': school_class,
        'selected_mode': mode,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': payments,
    }
    
    return render(request, 'finances/extra_fee_payment_list.html', context)

@login_required
def extra_fee_payment_detail(request, pk):
    """
    Vue pour afficher les détails d'un paiement de frais annexe
    """
    payment = get_object_or_404(ExtraFeePayment.objects.select_related('student', 'extra_fee', 'student__current_class'), pk=pk)
    return render(request, 'finances/extra_fee_payment_detail.html', {'payment': payment})

# ===== API AJAX POUR LES FORMULAIRES =====

@login_required
def get_classes_for_extra_fee(request, extra_fee_id):
    """
    Vue AJAX pour récupérer les classes d'un frais annexe
    """
    if not extra_fee_id:
        return JsonResponse({'classes': []})
    
    try:
        extra_fee = ExtraFee.objects.get(id=extra_fee_id)
        if extra_fee.apply_to_all_classes:
            classes = SchoolClass.objects.filter(year=extra_fee.year)
        else:
            classes = extra_fee.classes.all()
        
        classes_data = [{'id': c.id, 'name': c.name} for c in classes]
        return JsonResponse({'classes': classes_data})
    except ExtraFee.DoesNotExist:
        return JsonResponse({'classes': []})

@login_required
def get_students_for_class(request):
    """
    Vue AJAX pour récupérer les étudiants d'une classe (version GET)
    """
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'students': []})
    
    try:
        school_class = SchoolClass.objects.get(id=class_id)
        students = Student.objects.filter(current_class=school_class).order_by('last_name', 'first_name')
        students_data = [{'id': s.id, 'name': f"{s.last_name} {s.first_name}"} for s in students]
        return JsonResponse({'students': students_data})
    except SchoolClass.DoesNotExist:
        return JsonResponse({'students': []})


@login_required
def get_students_for_class_api(request, class_id):
    """
    Vue AJAX pour récupérer les étudiants d'une classe (version API avec paramètre)
    """
    if not class_id:
        return JsonResponse({'students': []})
    
    try:
        school_class = SchoolClass.objects.get(id=class_id)
        students = Student.objects.filter(current_class=school_class, is_active=True).order_by('last_name', 'first_name')
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'matricule': student.matricule,
                'current_class_name': student.current_class.name if student.current_class else 'N/A'
            })
        return JsonResponse({'students': students_data})
    except SchoolClass.DoesNotExist:
        return JsonResponse({'students': []})


@login_required
def extra_fee_amount(request, extra_fee_id):
    """
    Vue API pour récupérer le montant d'un frais annexe
    """
    try:
        extra_fee = ExtraFee.objects.get(id=extra_fee_id)
        amount = extra_fee.amount
        return JsonResponse({'amount': float(amount)})
    except ExtraFee.DoesNotExist:
        return JsonResponse({'amount': 0})


@login_required
def get_amount_for_extra_fee(request, extra_fee_id, class_id, student_id):
    """
    Vue API pour récupérer le montant d'un frais annexe pour une classe et un étudiant
    """
    try:
        extra_fee = ExtraFee.objects.get(id=extra_fee_id)
        school_class = SchoolClass.objects.get(id=class_id)
        student = Student.objects.get(id=student_id)
        
        # Vérifier que l'étudiant appartient à la classe
        if student.current_class != school_class:
            return JsonResponse({'amount': 0, 'error': 'Étudiant ne correspond pas à la classe'})
        
        # Récupérer le montant du frais annexe
        amount = extra_fee.get_amount_for_class(school_class)
        return JsonResponse({'amount': float(amount)})
    except (ExtraFee.DoesNotExist, SchoolClass.DoesNotExist, Student.DoesNotExist):
        return JsonResponse({'amount': 0, 'error': 'Données non trouvées'})

# ===== GÉNÉRATION DE FACTURES PDF =====

@login_required
def extra_fee_payment_receipt_pdf(request, pk):
    """
    Vue pour générer la facture PDF pour un paiement de frais annexe
    """
    payment = get_object_or_404(ExtraFeePayment.objects.select_related('student', 'extra_fee', 'student__current_class'), pk=pk)
    
    # Récupérer les informations de l'établissement
    try:
        school = School.objects.first()
        document_header = school.get_active_header() if school else None
        
        # Construire les URLs absolues pour les images
        logo_url = None
        signature_url = None
        
        if document_header:
            if document_header.logo:
                try:
                    logo_url = request.build_absolute_uri(document_header.logo.url)
                except Exception:
                    logo_url = None
            
            if document_header.signature:
                try:
                    signature_url = request.build_absolute_uri(document_header.signature.url)
                except Exception:
                    signature_url = None
    except:
        school = None
        document_header = None
        logo_url = None
        signature_url = None
    
    context = {
        'payment': payment,
        'school': school,
        'document_header': document_header,
        'logo_url': logo_url,
        'signature_url': signature_url,
        'current_year': CurrentSchoolYear.objects.first()
    }
    
    # Générer le PDF
    try:
        from weasyprint import HTML
        html_string = render_to_string('finances/extra_fee_payment_receipt_pdf.html', context)
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="facture_frais_annexe_{payment.id}.pdf"'
        return response
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF: {e}")
        messages.error(request, 'Erreur lors de la génération du PDF.')
        return redirect('finances:extra_fee_payment_detail', pk=pk)

# ===== GESTION DES TYPES DE FRAIS ANNEXES =====

@login_required
def extra_fee_type_list(request):
    """Liste des types de frais annexes"""
    types = ExtraFeeType.objects.all().order_by('name')
    
    # Statistiques
    total_types = types.count()
    active_types = types.filter(is_active=True).count()
    total_fees = ExtraFee.objects.count()
    
    context = {
        'types': types,
        'total_types': total_types,
        'active_types': active_types,
        'total_fees': total_fees
    }
    return render(request, 'finances/extra_fee_type_list.html', context)

@login_required
def extra_fee_type_create(request):
    """Créer un type de frais annexe"""
    if request.method == 'POST':
        form = ExtraFeeTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Type de frais annexe créé avec succès.')
            return redirect('finances:extra_fee_type_list')
    else:
        form = ExtraFeeTypeForm()
    
    return render(request, 'finances/extra_fee_type_form.html', {'form': form, 'title': 'Créer un type de frais annexe'})

@login_required
def extra_fee_type_update(request, pk):
    """Modifier un type de frais annexe"""
    fee_type = get_object_or_404(ExtraFeeType, pk=pk)
    if request.method == 'POST':
        form = ExtraFeeTypeForm(request.POST, instance=fee_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Type de frais annexe modifié avec succès.')
            return redirect('finances:extra_fee_type_list')
    else:
        form = ExtraFeeTypeForm(instance=fee_type)
    
    return render(request, 'finances/extra_fee_type_form.html', {'form': form, 'title': 'Modifier le type de frais annexe'})

@login_required
def extra_fee_type_delete(request, pk):
    """Supprimer un type de frais annexe"""
    fee_type = get_object_or_404(ExtraFeeType, pk=pk)
    if request.method == 'POST':
        fee_type.delete()
        messages.success(request, 'Type de frais annexe supprimé avec succès.')
        return redirect('finances:extra_fee_type_list')
    return render(request, 'finances/extra_fee_type_confirm_delete.html', {'fee_type': fee_type})


# ===== API POUR LA RECHERCHE D'ÉTUDIANTS =====

@login_required
def search_students_api(request):
    """API pour la recherche d'étudiants dans le formulaire de paiement des frais annexes"""
    query = request.GET.get('query', '')
    class_id = request.GET.get('class_id', '')
    
    if not query or not class_id:
        return JsonResponse({'students': []})
    
    try:
        # Rechercher les étudiants de la classe spécifiée
        students = Student.objects.filter(
            current_class_id=class_id,
            is_active=True
        ).filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(matricule__icontains=query)
        ).select_related('current_class')[:10]  # Limiter à 10 résultats
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'matricule': student.matricule,
                'current_class_name': student.current_class.name if student.current_class else 'N/A'
            })
        
        return JsonResponse({'students': students_data})
    except Exception as e:
        logger.error(f"Erreur lors de la recherche d'étudiants: {e}")
        return JsonResponse({'students': []})

@login_required
def get_classes_with_fee_structures(request):
    """
    Vue AJAX pour récupérer les classes avec leurs structures de frais
    """
    try:
        classes = SchoolClass.objects.filter(
            is_active=True
        ).select_related('level').prefetch_related('fee_structures').order_by('level__name', 'name')
        
        classes_data = []
        for school_class in classes:
            fee_structures = []
            for fs in school_class.fee_structures.all():
                fee_structures.append({
                    'id': fs.id,
                    'inscription_fee': float(fs.inscription_fee),
                    'tuition_total': float(fs.tuition_total),
                    'year': fs.year.annee,
                    'tranche_count': fs.tranches.count()
                })
            
            classes_data.append({
                'id': school_class.id,
                'name': school_class.name,
                'level_name': school_class.level.name,
                'display_name': f"{school_class.level.name} - {school_class.name}",
                'fee_structures': fee_structures
            })
        
        return JsonResponse({'classes': classes_data})
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des classes: {e}")
        return JsonResponse({'error': 'Erreur lors de la récupération des classes'})

@login_required
def get_students_for_class(request):
    """
    Vue pour récupérer les étudiants d'une classe pour les paiements en lot
    """
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'students': []})
    
    try:
        students = Student.objects.filter(
            current_class_id=class_id, is_active=True
        ).values('id', 'first_name', 'last_name', 'matricule')
        
        # Ajouter le nom complet pour chaque étudiant
        students_list = []
        for student in students:
            student_data = {
                'id': student['id'],
                'first_name': student['first_name'],
                'last_name': student['last_name'],
                'matricule': student['matricule'],
                'name': f"{student['last_name'].upper()} {student['first_name']}"
            }
            students_list.append(student_data)
        
        return JsonResponse({'students': students_list})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des étudiants: {e}")
        return JsonResponse({'error': 'Erreur lors de la récupération des étudiants'}, status=500)

@login_required
def get_tranches_for_student(request):
    """
    Vue AJAX pour récupérer les tranches d'un étudiant (non payées)
    """
    student_id = request.GET.get('student_id')
    if not student_id:
        return JsonResponse({'error': 'ID étudiant manquant'}, status=400)
    
    try:
        student = Student.objects.select_related('current_class').get(id=student_id, is_active=True)
        
        if not student.current_class:
            return JsonResponse({'tranches': []})
        
        # Récupérer les tranches pour la classe de l'étudiant
        tranches = FeeTranche.objects.filter(
            fee_structure__school_class=student.current_class
        ).select_related('fee_structure', 'fee_structure__year').values(
            'id', 'number', 'amount', 'due_date', 
            'fee_structure__year__annee'
        )
        
        tranches_list = []
        for tranche in tranches:
            # Calculer le montant payé pour cette tranche
            payments_sum = TranchePayment.objects.filter(
                student=student, 
                tranche_id=tranche['id']
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            # Calculer les remises pour cette tranche
            discounts_sum = FeeDiscount.objects.filter(
                student=student, 
                tranche_id=tranche['id']
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            # Calculer les remboursements pour cette tranche
            refunds_sum = PaymentRefund.objects.filter(
                payment__student=student, 
                payment__tranche_id=tranche['id']
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            # Calculer le solde restant
            total_paid = payments_sum + discounts_sum - refunds_sum
            remaining = float(tranche['amount']) - float(total_paid)
            
            # Ne retourner que les tranches avec un solde restant > 0
            if remaining > 0:
                tranches_list.append({
                    'id': tranche['id'],
                    'number': tranche['number'],
                    'amount': float(tranche['amount']),
                    'remaining': remaining,
                    'paid': float(total_paid),
                    'due_date': tranche['due_date'].strftime('%d/%m/%Y'),
                    'fee_structure': {
                        'year': tranche['fee_structure__year__annee']
                    }
                })
        
        return JsonResponse({'tranches': tranches_list})
        
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Étudiant non trouvé'}, status=404)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tranches pour l'étudiant: {e}")
        return JsonResponse({'error': 'Erreur lors de la récupération des tranches'}, status=500)

@login_required
def export_financial_report(request):
    """
    Vue pour exporter le rapport financier en PDF
    """
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Récupérer les paramètres de période
    period = request.GET.get('period', 'this_month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Calculer les dates selon la période
    today = timezone.now().date()
    
    if period == 'today':
        start_date = today
        end_date = today
        period_name = "Aujourd'hui"
    elif period == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = start_date
        period_name = "Hier"
    elif period == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        period_name = "Semaine en cours"
    elif period == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=6)
        period_name = "Semaine dernière"
    elif period == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
        period_name = "Mois en cours"
    elif period == 'last_month':
        if today.month == 1:
            start_date = today.replace(year=today.year-1, month=12, day=1)
        else:
            start_date = today.replace(month=today.month-1, day=1)
        end_date = start_date.replace(day=28) + timedelta(days=4)
        end_date = end_date.replace(day=1) - timedelta(days=1)
        period_name = "Mois dernier"
    elif period == 'custom' and start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        period_name = f"Du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"
    else:
        # Par défaut: mois en cours
        start_date = today.replace(day=1)
        end_date = today
        period_name = "Mois en cours"
    
    # Récupérer les données financières pour la période
    from students.models import Student
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    if not current_year:
        return HttpResponse("Aucune année scolaire active", status=400)
    
    # Récupérer les 5 derniers paiements (tous types confondus)
    recent_payments = []
    
    # Derniers paiements de tranches
    recent_tranche_payments = TranchePayment.objects.select_related(
        'student', 'tranche', 'tranche__fee_structure'
    ).order_by('-payment_date')[:5]
    
    # Derniers paiements d'inscription
    recent_inscription_payments = InscriptionPayment.objects.select_related(
        'student', 'fee_structure'
    ).order_by('-payment_date')[:5]
    
    # Combiner et trier par date
    for payment in recent_tranche_payments:
        recent_payments.append({
            'type': 'tranche',
            'payment': payment,
            'date': payment.payment_date,
            'amount': payment.amount,
            'student': payment.student,
            'description': f"Tranche {payment.tranche.number}" if payment.tranche else "Tranche"
        })
    
    for payment in recent_inscription_payments:
        recent_payments.append({
            'type': 'inscription',
            'payment': payment,
            'date': payment.payment_date,
            'amount': payment.amount,
            'student': payment.student,
            'description': "Frais d'inscription"
        })
    
    # Trier par date (plus récent en premier) et prendre les 5 premiers
    recent_payments.sort(key=lambda x: x['date'], reverse=True)
    recent_payments = recent_payments[:5]
    
    # Récupérer les paiements de la période
    payments = TranchePayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'tranche', 'tranche__fee_structure').order_by('-payment_date')
    
    inscription_payments = InscriptionPayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'fee_structure').order_by('-payment_date')
    
    # Récupérer les remises de la période
    discounts = FeeDiscount.objects.filter(
        granted_at__range=[start_date, end_date]
    ).select_related('student').order_by('-granted_at')
    
    # Calculer les totaux
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_inscription_payments = inscription_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_all_payments = total_payments + total_inscription_payments
    total_discounts = discounts.aggregate(total=Sum('amount'))['total'] or 0
    
    # Créer la liste complète des paiements pour le PDF (tous types confondus)
    all_payments = []
    
    # Ajouter les paiements de tranches
    for payment in payments[:50]:  # Limiter pour le PDF
        all_payments.append({
            'type': 'tranche',
            'payment': payment,
            'date': payment.payment_date,
            'amount': payment.amount,
            'student': payment.student,
            'description': f"Tranche {payment.tranche.number}" if payment.tranche else "Tranche"
        })
    
    # Ajouter les paiements d'inscription
    for payment in inscription_payments[:50]:  # Limiter pour le PDF
        all_payments.append({
            'type': 'inscription',
            'payment': payment,
            'date': payment.payment_date,
            'amount': payment.amount,
            'student': payment.student,
            'description': "Frais d'inscription"
        })
    
    # Trier par date (plus récent en premier)
    all_payments.sort(key=lambda x: x['date'], reverse=True)
    
    # Paiements par mode avec comptage
    payments_by_mode = payments.values('mode').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Calculer les pourcentages pour les paiements par mode
    for payment in payments_by_mode:
        if total_all_payments > 0:
            payment['percentage'] = (payment['total'] / total_all_payments) * 100
        else:
            payment['percentage'] = 0
    
    # Statistiques par classe
    from classes.models import SchoolClass
    from students.models import Student
    
    class_statistics = []
    classes = SchoolClass.objects.all()
    
    for school_class in classes:
        # Étudiants inscrits dans cette classe
        enrolled_students = Student.objects.filter(current_class=school_class).count()
        
        # Paiements d'inscription pour cette classe
        class_inscription_payments = inscription_payments.filter(
            student__current_class=school_class
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Paiements de scolarité pour cette classe
        class_tuition_payments = payments.filter(
            student__current_class=school_class
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Total des paiements pour cette classe
        class_total_payments = class_inscription_payments + class_tuition_payments
        
        # Remises pour cette classe
        class_discounts = discounts.filter(
            student__current_class=school_class
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calcul du taux de recouvrement
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        if fee_structure and enrolled_students > 0:
            expected_amount = (fee_structure.inscription_fee + fee_structure.tuition_total) * enrolled_students
            recovery_rate = ((class_total_payments - class_discounts) / expected_amount * 100) if expected_amount > 0 else 0
        else:
            recovery_rate = 0
        
        class_statistics.append({
            'class_name': school_class.name,
            'enrolled_students': enrolled_students,
            'inscription_payments': class_inscription_payments,
            'tuition_payments': class_tuition_payments,
            'total_payments': class_total_payments,
            'discounts': class_discounts,
            'recovery_rate': recovery_rate,
        })
    
    # Calculer les montants dus par type
    total_inscription_due = 0
    total_tuition_due = 0
    
    for school_class in classes:
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        if fee_structure:
            enrolled_students = Student.objects.filter(current_class=school_class).count()
            total_inscription_due += fee_structure.inscription_fee * enrolled_students
            total_tuition_due += fee_structure.tuition_total * enrolled_students
    
    # Calculer les taux de paiement par type (pourcentage payé vs dû)
    inscription_payment_rate = (total_inscription_payments / total_inscription_due * 100) if total_inscription_due > 0 else 0
    tuition_payment_rate = (total_payments / total_tuition_due * 100) if total_tuition_due > 0 else 0
    
    # Calculer les pourcentages de répartition (part de chaque type dans le total reçu)
    inscription_percentage = (total_inscription_payments / total_all_payments * 100) if total_all_payments > 0 else 0
    tuition_percentage = (total_payments / total_all_payments * 100) if total_all_payments > 0 else 0
    
    # Calculer le reste à payer (montant dû - paiements reçus + remises)
    total_due = 0
    total_students = 0
    for school_class in classes:
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        if fee_structure:
            enrolled_students = Student.objects.filter(current_class=school_class).count()
            total_students += enrolled_students
            total_due += (fee_structure.inscription_fee + fee_structure.tuition_total) * enrolled_students
    
    total_remaining = total_due - total_all_payments + total_discounts
    
    # Calculer les pourcentages pour le dashboard
    recovery_rate = ((total_all_payments - total_discounts) / total_due * 100) if total_due > 0 else 0
    remaining_percentage = (total_remaining / total_due * 100) if total_due > 0 else 0
    discount_percentage = (total_discounts / total_all_payments * 100) if total_all_payments > 0 else 0
    
    # Récupérer les informations de l'école
    school = None
    try:
        school = School.objects.first()
    except:
        school = None
    
    # Récupérer les paiements de la période
    payments = TranchePayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'tranche', 'tranche__fee_structure').order_by('-payment_date')
    
    # Paiements d'inscription de la période
    inscription_payments = InscriptionPayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'fee_structure').order_by('-payment_date')
    
    # Remises de la période
    discounts = FeeDiscount.objects.filter(
        granted_at__range=[start_date, end_date]
    ).select_related('student')
    
    # Calculs
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_inscription_payments = inscription_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_all_payments = total_payments + total_inscription_payments
    total_discounts = discounts.aggregate(total=Sum('amount'))['total'] or 0
    
    # Paiements par mode avec comptage
    payments_by_mode = payments.values('mode').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Calculer les pourcentages pour les paiements par mode
    for payment in payments_by_mode:
        if total_all_payments > 0:
            payment['percentage'] = (payment['total'] / total_all_payments) * 100
        else:
            payment['percentage'] = 0
    
    # Statistiques par classe
    from classes.models import SchoolClass
    from students.models import Student
    
    class_statistics = []
    classes = SchoolClass.objects.all()
    
    for school_class in classes:
        # Étudiants inscrits dans cette classe
        enrolled_students = Student.objects.filter(current_class=school_class).count()
        
        # Paiements d'inscription pour cette classe
        class_inscription_payments = inscription_payments.filter(
            student__current_class=school_class
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Paiements de scolarité pour cette classe
        class_tuition_payments = payments.filter(
            student__current_class=school_class
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Total des paiements pour cette classe
        class_total_payments = class_inscription_payments + class_tuition_payments
        
        # Remises pour cette classe
        class_discounts = discounts.filter(
            student__current_class=school_class
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calcul du taux de recouvrement
        # Montant dû = (frais d'inscription + scolarité) * nombre d'étudiants inscrits
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        if fee_structure and enrolled_students > 0:
            expected_amount = (fee_structure.inscription_fee + fee_structure.tuition_total) * enrolled_students
            recovery_rate = ((class_total_payments - class_discounts) / expected_amount * 100) if expected_amount > 0 else 0
        else:
            recovery_rate = 0
        
        class_statistics.append({
            'class_name': school_class.name,
            'enrolled_students': enrolled_students,
            'inscription_payments': class_inscription_payments,
            'tuition_payments': class_tuition_payments,
            'total_payments': class_total_payments,
            'discounts': class_discounts,
            'recovery_rate': recovery_rate,
        })
    
    # Calculer les montants dus par type
    total_inscription_due = 0
    total_tuition_due = 0
    
    for school_class in classes:
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        if fee_structure:
            enrolled_students = Student.objects.filter(current_class=school_class).count()
            total_inscription_due += fee_structure.inscription_fee * enrolled_students
            total_tuition_due += fee_structure.tuition_total * enrolled_students
    
    # Calculer les taux de paiement par type (pourcentage payé vs dû)
    inscription_payment_rate = (total_inscription_payments / total_inscription_due * 100) if total_inscription_due > 0 else 0
    tuition_payment_rate = (total_payments / total_tuition_due * 100) if total_tuition_due > 0 else 0
    
    # Calculer les pourcentages de répartition (part de chaque type dans le total reçu)
    inscription_percentage = (total_inscription_payments / total_all_payments * 100) if total_all_payments > 0 else 0
    tuition_percentage = (total_payments / total_all_payments * 100) if total_all_payments > 0 else 0
    
    # Paiements par jour
    payments_by_day = payments.values('payment_date').annotate(
        total=Sum('amount')
    ).order_by('payment_date')
    
    # Récupérer les informations de l'école
    try:
        from school.models import School
        school = School.objects.first()
    except:
        school = None
    
    # Calculer le reste à payer (montant dû - paiements reçus + remises)
    total_due = 0
    total_students = 0
    for school_class in classes:
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        if fee_structure:
            enrolled_students = Student.objects.filter(current_class=school_class).count()
            total_students += enrolled_students
            total_due += (fee_structure.inscription_fee + fee_structure.tuition_total) * enrolled_students
    
    total_remaining = total_due - total_all_payments + total_discounts
    
    # Calculer les pourcentages pour le dashboard
    recovery_rate = ((total_all_payments - total_discounts) / total_due * 100) if total_due > 0 else 0
    remaining_percentage = (total_remaining / total_due * 100) if total_due > 0 else 0
    discount_percentage = (total_discounts / total_all_payments * 100) if total_all_payments > 0 else 0
    
    # Préparer le contexte
    context = {
        'school': school,
        'period_name': period_name,
        'start_date': start_date,
        'end_date': end_date,
        'current_year': current_year,
        'total_all_payments': total_all_payments,
        'total_payments': total_payments,
        'total_inscription_payments': total_inscription_payments,
        'total_discounts': total_discounts,
        'total_remaining': total_remaining,
        'total_students': total_students,
        'recovery_rate': recovery_rate,
        'remaining_percentage': remaining_percentage,
        'discount_percentage': discount_percentage,
        'payments_by_mode': payments_by_mode,
        'class_statistics': class_statistics,
        'inscription_percentage': inscription_percentage,
        'tuition_percentage': tuition_percentage,
        'inscription_payment_rate': inscription_payment_rate,
        'tuition_payment_rate': tuition_payment_rate,
        'total_inscription_due': total_inscription_due,
        'total_tuition_due': total_tuition_due,
        'payments': payments[:50],  # Limiter pour le PDF
        'inscription_payments': inscription_payments[:50],
        'all_payments': all_payments,  # Liste combinée pour le PDF
        'discounts': discounts[:50],
        'recent_payments': recent_payments,
        'generated_at': timezone.now(),
    }
    
    # Générer le HTML
    html_string = render_to_string('finances/financial_report_pdf.html', context)
    
    # Configuration des polices
    font_config = FontConfiguration()
    
    # Générer le PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf(font_config=font_config)
    
    # Créer la réponse HTTP
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_financier_{period}_{start_date}_{end_date}.pdf"'
    
    return response
