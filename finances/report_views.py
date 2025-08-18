from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from datetime import datetime, timedelta

from .models import (
    SchoolYear, FeeStructure, FeeTranche, TranchePayment, 
    InscriptionPayment, FeeDiscount, Moratorium
)
from classes.models import SchoolClass
from students.models import Student
from school.models import School


# ==================== FONCTIONS UTILITAIRES POUR LES RAPPORTS ====================

def get_period_dates(request):
    """Fonction utilitaire pour calculer les dates selon la période sélectionnée"""
    period = request.GET.get('period', 'this_month')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
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
        start_date = today.replace(day=1)
        end_date = today
        period_name = "Mois en cours"
    
    return start_date, end_date, period_name


@login_required
def reports_dashboard(request):
    """Dashboard principal des rapports financiers"""
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    classes = SchoolClass.objects.all()
    
    # Statistiques rapides
    total_students = Student.objects.count()
    total_classes = classes.count()
    
    # Paiements récents
    recent_payments = TranchePayment.objects.select_related('student', 'tranche').order_by('-payment_date')[:5]
    recent_inscriptions = InscriptionPayment.objects.select_related('student').order_by('-payment_date')[:5]
    
    # Retards
    overdue_count = 0
    for school_class in classes:
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        if fee_structure:
            for tranche in fee_structure.tranches.all():
                if tranche.due_date < timezone.now().date():
                    overdue_count += TranchePayment.objects.filter(
                        tranche=tranche,
                        amount__lt=tranche.amount
                    ).count()
    
    context = {
        'current_year': current_year,
        'classes': classes,
        'total_students': total_students,
        'total_classes': total_classes,
        'recent_payments': recent_payments,
        'recent_inscriptions': recent_inscriptions,
        'overdue_count': overdue_count,
    }
    
    return render(request, 'finances/reports_dashboard.html', context)


# ==================== RAPPORTS D'INSCRIPTION ====================

@login_required
def inscriptions_report(request):
    """Rapport des inscriptions"""
    start_date, end_date, period_name = get_period_dates(request)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les inscriptions de la période
    inscriptions = InscriptionPayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'student__current_class', 'fee_structure').order_by('-payment_date')
    
    # Statistiques par classe
    class_stats = []
    classes = SchoolClass.objects.all()
    
    for school_class in classes:
        class_inscriptions = inscriptions.filter(student__current_class=school_class)
        total_amount = class_inscriptions.aggregate(total=Sum('amount'))['total'] or 0
        student_count = Student.objects.filter(current_class=school_class).count()
        
        # Calculer le taux de paiement d'inscription
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        expected_amount = fee_structure.inscription_fee * student_count if fee_structure else 0
        payment_rate = (total_amount / expected_amount * 100) if expected_amount > 0 else 0
        
        class_stats.append({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'student_count': student_count,
            'inscription_count': class_inscriptions.count(),
            'total_amount': total_amount,
            'expected_amount': expected_amount,
            'payment_rate': payment_rate,
        })
    
    # Statistiques globales
    total_inscriptions = inscriptions.count()
    total_amount = inscriptions.aggregate(total=Sum('amount'))['total'] or 0
    
    # Paiements par mode
    payments_by_mode = inscriptions.values('mode').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'period_name': period_name,
        'start_date': start_date,
        'end_date': end_date,
        'current_year': current_year,
        'inscriptions': inscriptions,
        'class_stats': class_stats,
        'total_inscriptions': total_inscriptions,
        'total_amount': total_amount,
        'payments_by_mode': payments_by_mode,
    }
    
    return render(request, 'finances/inscriptions_report.html', context)


@login_required
def inscriptions_report_class(request, class_id):
    """Rapport des inscriptions pour une classe spécifique"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    start_date, end_date, period_name = get_period_dates(request)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les inscriptions de la classe pour la période
    inscriptions = InscriptionPayment.objects.filter(
        student__current_class=school_class,
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'fee_structure').order_by('-payment_date')
    
    # Étudiants de la classe
    students = Student.objects.filter(current_class=school_class)
    
    # Étudiants sans paiement d'inscription
    students_without_payment = []
    for student in students:
        if not InscriptionPayment.objects.filter(student=student).exists():
            students_without_payment.append(student)
    
    # Statistiques
    total_students = students.count()
    total_inscriptions = inscriptions.count()
    total_amount = inscriptions.aggregate(total=Sum('amount'))['total'] or 0
    
    # Taux de paiement
    fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
    expected_amount = fee_structure.inscription_fee * total_students if fee_structure else 0
    payment_rate = (total_amount / expected_amount * 100) if expected_amount > 0 else 0
    
    context = {
        'school_class': school_class,
        'period_name': period_name,
        'start_date': start_date,
        'end_date': end_date,
        'current_year': current_year,
        'inscriptions': inscriptions,
        'students': students,
        'students_without_payment': students_without_payment,
        'total_students': total_students,
        'total_inscriptions': total_inscriptions,
        'total_amount': total_amount,
        'expected_amount': expected_amount,
        'payment_rate': payment_rate,
    }
    
    return render(request, 'finances/inscriptions_report_class.html', context)


@login_required
def export_inscriptions_report(request):
    """Export PDF du rapport d'inscriptions"""
    start_date, end_date, period_name = get_period_dates(request)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les données
    inscriptions = InscriptionPayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'student__current_class', 'fee_structure').order_by('-payment_date')
    
    # Statistiques par classe
    class_stats = []
    classes = SchoolClass.objects.all()
    
    for school_class in classes:
        class_inscriptions = inscriptions.filter(student__current_class=school_class)
        total_amount = class_inscriptions.aggregate(total=Sum('amount'))['total'] or 0
        student_count = Student.objects.filter(current_class=school_class).count()
        
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        expected_amount = fee_structure.inscription_fee * student_count if fee_structure else 0
        payment_rate = (total_amount / expected_amount * 100) if expected_amount > 0 else 0
        
        class_stats.append({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'student_count': student_count,
            'inscription_count': class_inscriptions.count(),
            'total_amount': total_amount,
            'expected_amount': expected_amount,
            'payment_rate': payment_rate,
        })
    
    # Statistiques globales
    total_inscriptions = inscriptions.count()
    total_amount = inscriptions.aggregate(total=Sum('amount'))['total'] or 0
    
    # Récupérer les informations de l'école
    school = School.objects.first()
    
    context = {
        'school': school,
        'period_name': period_name,
        'start_date': start_date,
        'end_date': end_date,
        'current_year': current_year,
        'inscriptions': inscriptions,
        'class_stats': class_stats,
        'total_inscriptions': total_inscriptions,
        'total_amount': total_amount,
        'generated_at': timezone.now(),
    }
    
    # Générer le PDF
    html_string = render_to_string('finances/inscriptions_report_pdf.html', context)
    pdf = HTML(string=html_string).write_pdf()
    
    # Retourner le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_inscriptions_{period_name}.pdf"'
    return response


# ==================== RAPPORTS DE SCOLARITÉ ====================

@login_required
def tuition_report(request):
    """Rapport de scolarité global"""
    start_date, end_date, period_name = get_period_dates(request)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les paiements de scolarité de la période
    payments = TranchePayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'student__current_class', 'tranche', 'tranche__fee_structure').order_by('-payment_date')
    
    # Statistiques par classe
    class_stats = []
    classes = SchoolClass.objects.all()
    
    for school_class in classes:
        class_payments = payments.filter(student__current_class=school_class)
        total_amount = class_payments.aggregate(total=Sum('amount'))['total'] or 0
        student_count = Student.objects.filter(current_class=school_class).count()
        
        # Calculer le taux de recouvrement
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        expected_amount = fee_structure.tuition_total * student_count if fee_structure else 0
        recovery_rate = (total_amount / expected_amount * 100) if expected_amount > 0 else 0
        
        class_stats.append({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'student_count': student_count,
            'payment_count': class_payments.count(),
            'total_amount': total_amount,
            'expected_amount': expected_amount,
            'recovery_rate': recovery_rate,
        })
    
    # Statistiques globales
    total_payments = payments.count()
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Paiements par tranche
    payments_by_tranche = payments.values('tranche__number').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('tranche__number')
    
    # Paiements par mode
    payments_by_mode = payments.values('mode').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'period_name': period_name,
        'start_date': start_date,
        'end_date': end_date,
        'current_year': current_year,
        'payments': payments,
        'class_stats': class_stats,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'payments_by_tranche': payments_by_tranche,
        'payments_by_mode': payments_by_mode,
    }
    
    return render(request, 'finances/tuition_report.html', context)


@login_required
def tuition_report_class(request, class_id):
    """Rapport de scolarité pour une classe spécifique"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    start_date, end_date, period_name = get_period_dates(request)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les paiements de la classe pour la période
    payments = TranchePayment.objects.filter(
        student__current_class=school_class,
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'tranche', 'tranche__fee_structure').order_by('-payment_date')
    
    # Étudiants de la classe
    students = Student.objects.filter(current_class=school_class)
    
    # Statistiques par étudiant
    student_stats = []
    for student in students:
        student_payments = payments.filter(student=student)
        total_paid = student_payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculer le montant dû
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        amount_due = fee_structure.tuition_total if fee_structure else 0
        remaining = amount_due - total_paid
        
        student_stats.append({
            'student': student,
            'total_paid': total_paid,
            'amount_due': amount_due,
            'remaining': remaining,
            'payment_rate': (total_paid / amount_due * 100) if amount_due > 0 else 0,
        })
    
    # Statistiques globales
    total_students = students.count()
    total_payments = payments.count()
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Taux de recouvrement
    fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
    expected_amount = fee_structure.tuition_total * total_students if fee_structure else 0
    recovery_rate = (total_amount / expected_amount * 100) if expected_amount > 0 else 0
    
    context = {
        'school_class': school_class,
        'period_name': period_name,
        'start_date': start_date,
        'end_date': end_date,
        'current_year': current_year,
        'payments': payments,
        'students': students,
        'student_stats': student_stats,
        'total_students': total_students,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'expected_amount': expected_amount,
        'recovery_rate': recovery_rate,
    }
    
    return render(request, 'finances/tuition_report_class.html', context)


@login_required
def export_tuition_report(request):
    """Export PDF du rapport de scolarité"""
    start_date, end_date, period_name = get_period_dates(request)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les données
    payments = TranchePayment.objects.filter(
        payment_date__range=[start_date, end_date]
    ).select_related('student', 'student__current_class', 'tranche', 'tranche__fee_structure').order_by('-payment_date')
    
    # Statistiques par classe
    class_stats = []
    classes = SchoolClass.objects.all()
    
    for school_class in classes:
        class_payments = payments.filter(student__current_class=school_class)
        total_amount = class_payments.aggregate(total=Sum('amount'))['total'] or 0
        student_count = Student.objects.filter(current_class=school_class).count()
        
        fee_structure = FeeStructure.objects.filter(school_class=school_class).first()
        expected_amount = fee_structure.tuition_total * student_count if fee_structure else 0
        recovery_rate = (total_amount / expected_amount * 100) if expected_amount > 0 else 0
        
        class_stats.append({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'student_count': student_count,
            'payment_count': class_payments.count(),
            'total_amount': total_amount,
            'expected_amount': expected_amount,
            'recovery_rate': recovery_rate,
        })
    
    # Statistiques globales
    total_payments = payments.count()
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Récupérer les informations de l'école
    school = School.objects.first()
    
    context = {
        'school': school,
        'period_name': period_name,
        'start_date': start_date,
        'end_date': end_date,
        'current_year': current_year,
        'payments': payments,
        'class_stats': class_stats,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'generated_at': timezone.now(),
    }
    
    # Générer le PDF
    html_string = render_to_string('finances/tuition_report_pdf.html', context)
    pdf = HTML(string=html_string).write_pdf()
    
    # Retourner le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_scolarite_{period_name}.pdf"'
    return response


# ==================== RAPPORTS DE RETARDS ====================

@login_required
def overdue_report(request):
    """Rapport des retards d'échéance"""
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer toutes les tranches en retard
    today = timezone.now().date()
    overdue_tranches = FeeTranche.objects.filter(
        due_date__lt=today,
        fee_structure__year=current_year
    ).select_related('fee_structure', 'fee_structure__school_class')
    
    # Statistiques par classe
    class_stats = []
    classes = SchoolClass.objects.all()
    
    for school_class in classes:
        class_overdue = []
        total_overdue = 0
        student_count = 0
        
        for tranche in overdue_tranches.filter(fee_structure__school_class=school_class):
            # Étudiants en retard pour cette tranche
            students_in_class = Student.objects.filter(current_class=school_class)
            
            for student in students_in_class:
                payment = TranchePayment.objects.filter(student=student, tranche=tranche).first()
                paid_amount = payment.amount if payment else 0
                overdue_amount = tranche.amount - paid_amount
                
                if overdue_amount > 0:
                    days_overdue = (today - tranche.due_date).days
                    class_overdue.append({
                        'student': student,
                        'tranche': tranche,
                        'paid_amount': paid_amount,
                        'overdue_amount': overdue_amount,
                        'days_overdue': days_overdue,
                        'severity': 'high' if days_overdue > 30 else 'medium' if days_overdue > 7 else 'low'
                    })
                    total_overdue += overdue_amount
                    student_count += 1
        
        class_stats.append({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'overdue_students': student_count,
            'total_overdue': total_overdue,
            'overdue_details': class_overdue,
        })
    
    # Statistiques globales
    total_overdue_students = sum(stat['overdue_students'] for stat in class_stats)
    total_overdue_amount = sum(stat['total_overdue'] for stat in class_stats)
    
    context = {
        'current_year': current_year,
        'class_stats': class_stats,
        'total_overdue_students': total_overdue_students,
        'total_overdue_amount': total_overdue_amount,
        'today': today,
    }
    
    return render(request, 'finances/overdue_report.html', context)


@login_required
def overdue_report_class(request, class_id):
    """Rapport des retards pour une classe spécifique"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les tranches en retard pour cette classe
    today = timezone.now().date()
    overdue_tranches = FeeTranche.objects.filter(
        due_date__lt=today,
        fee_structure__school_class=school_class,
        fee_structure__year=current_year
    ).select_related('fee_structure')
    
    # Détail des retards par étudiant
    overdue_students = []
    students = Student.objects.filter(current_class=school_class)
    
    for student in students:
        student_overdue = []
        total_overdue = 0
        
        for tranche in overdue_tranches:
            payment = TranchePayment.objects.filter(student=student, tranche=tranche).first()
            paid_amount = payment.amount if payment else 0
            overdue_amount = tranche.amount - paid_amount
            
            if overdue_amount > 0:
                days_overdue = (today - tranche.due_date).days
                student_overdue.append({
                    'tranche': tranche,
                    'paid_amount': paid_amount,
                    'overdue_amount': overdue_amount,
                    'days_overdue': days_overdue,
                    'severity': 'high' if days_overdue > 30 else 'medium' if days_overdue > 7 else 'low'
                })
                total_overdue += overdue_amount
        
        if student_overdue:
            overdue_students.append({
                'student': student,
                'overdue_details': student_overdue,
                'total_overdue': total_overdue,
            })
    
    # Statistiques
    total_overdue_students = len(overdue_students)
    total_overdue_amount = sum(student['total_overdue'] for student in overdue_students)
    
    context = {
        'school_class': school_class,
        'current_year': current_year,
        'overdue_students': overdue_students,
        'total_overdue_students': total_overdue_students,
        'total_overdue_amount': total_overdue_amount,
        'today': today,
    }
    
    return render(request, 'finances/overdue_report_class.html', context)


@login_required
def export_overdue_report(request):
    """Export PDF du rapport des retards"""
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les données (même logique que overdue_report)
    today = timezone.now().date()
    overdue_tranches = FeeTranche.objects.filter(
        due_date__lt=today,
        fee_structure__year=current_year
    ).select_related('fee_structure', 'fee_structure__school_class')
    
    # Statistiques par classe
    class_stats = []
    classes = SchoolClass.objects.all()
    
    for school_class in classes:
        class_overdue = []
        total_overdue = 0
        student_count = 0
        
        for tranche in overdue_tranches.filter(fee_structure__school_class=school_class):
            students_in_class = Student.objects.filter(current_class=school_class)
            
            for student in students_in_class:
                payment = TranchePayment.objects.filter(student=student, tranche=tranche).first()
                paid_amount = payment.amount if payment else 0
                overdue_amount = tranche.amount - paid_amount
                
                if overdue_amount > 0:
                    days_overdue = (today - tranche.due_date).days
                    class_overdue.append({
                        'student': student,
                        'tranche': tranche,
                        'paid_amount': paid_amount,
                        'overdue_amount': overdue_amount,
                        'days_overdue': days_overdue,
                        'severity': 'high' if days_overdue > 30 else 'medium' if days_overdue > 7 else 'low'
                    })
                    total_overdue += overdue_amount
                    student_count += 1
        
        class_stats.append({
            'class_id': school_class.id,
            'class_name': school_class.name,
            'overdue_students': student_count,
            'total_overdue': total_overdue,
            'overdue_details': class_overdue,
        })
    
    # Statistiques globales
    total_overdue_students = sum(stat['overdue_students'] for stat in class_stats)
    total_overdue_amount = sum(stat['total_overdue'] for stat in class_stats)
    
    # Récupérer les informations de l'école
    school = School.objects.first()
    
    context = {
        'school': school,
        'current_year': current_year,
        'class_stats': class_stats,
        'total_overdue_students': total_overdue_students,
        'total_overdue_amount': total_overdue_amount,
        'today': today,
        'generated_at': timezone.now(),
    }
    
    # Générer le PDF
    html_string = render_to_string('finances/overdue_report_pdf.html', context)
    pdf = HTML(string=html_string).write_pdf()
    
    # Retourner le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_retards_{today}.pdf"'
    return response


# ==================== RAPPORTS DE PERFORMANCE ====================

@login_required
def performance_report(request):
    """Rapport de performance financière"""
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Indicateurs clés
    total_students = Student.objects.count()
    total_classes = SchoolClass.objects.count()
    
    # Paiements de l'année
    year_payments = TranchePayment.objects.filter(
        tranche__fee_structure__year=current_year
    )
    year_inscriptions = InscriptionPayment.objects.filter(
        fee_structure__year=current_year
    )
    
    total_tuition_paid = year_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_inscription_paid = year_inscriptions.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = total_tuition_paid + total_inscription_paid
    
    # Montants dus
    total_due = 0
    for school_class in SchoolClass.objects.all():
        fee_structure = FeeStructure.objects.filter(school_class=school_class, year=current_year).first()
        if fee_structure:
            student_count = Student.objects.filter(current_class=school_class).count()
            total_due += (fee_structure.inscription_fee + fee_structure.tuition_total) * student_count
    
    # Taux de recouvrement
    recovery_rate = (total_paid / total_due * 100) if total_due > 0 else 0
    
    # Évolution mensuelle
    monthly_data = []
    for month in range(1, 13):
        month_payments = year_payments.filter(payment_date__month=month)
        month_inscriptions = year_inscriptions.filter(payment_date__month=month)
        
        month_total = (month_payments.aggregate(total=Sum('amount'))['total'] or 0) + \
                     (month_inscriptions.aggregate(total=Sum('amount'))['total'] or 0)
        
        monthly_data.append({
            'month': month,
            'month_name': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 
                          'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'][month-1],
            'total': month_total,
        })
    
    # Alertes
    alerts = []
    
    # Classes avec faible taux de recouvrement
    for school_class in SchoolClass.objects.all():
        fee_structure = FeeStructure.objects.filter(school_class=school_class, year=current_year).first()
        if fee_structure:
            student_count = Student.objects.filter(current_class=school_class).count()
            expected = (fee_structure.inscription_fee + fee_structure.tuition_total) * student_count
            
            class_payments = year_payments.filter(student__current_class=school_class)
            class_inscriptions = year_inscriptions.filter(student__current_class=school_class)
            received = (class_payments.aggregate(total=Sum('amount'))['total'] or 0) + \
                      (class_inscriptions.aggregate(total=Sum('amount'))['total'] or 0)
            
            class_rate = (received / expected * 100) if expected > 0 else 0
            if class_rate < 70:
                alerts.append({
                    'type': 'low_recovery',
                    'message': f'Classe {school_class.name}: Taux de recouvrement faible ({class_rate:.1f}%)',
                    'severity': 'high' if class_rate < 50 else 'medium'
                })
    
    context = {
        'current_year': current_year,
        'total_students': total_students,
        'total_classes': total_classes,
        'total_paid': total_paid,
        'total_due': total_due,
        'recovery_rate': recovery_rate,
        'monthly_data': monthly_data,
        'alerts': alerts,
    }
    
    return render(request, 'finances/performance_report.html', context)


@login_required
def export_performance_report(request):
    """Export PDF du rapport de performance"""
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les données (même logique que performance_report)
    total_students = Student.objects.count()
    total_classes = SchoolClass.objects.count()
    
    year_payments = TranchePayment.objects.filter(tranche__fee_structure__year=current_year)
    year_inscriptions = InscriptionPayment.objects.filter(fee_structure__year=current_year)
    
    total_tuition_paid = year_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_inscription_paid = year_inscriptions.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = total_tuition_paid + total_inscription_paid
    
    total_due = 0
    for school_class in SchoolClass.objects.all():
        fee_structure = FeeStructure.objects.filter(school_class=school_class, year=current_year).first()
        if fee_structure:
            student_count = Student.objects.filter(current_class=school_class).count()
            total_due += (fee_structure.inscription_fee + fee_structure.tuition_total) * student_count
    
    recovery_rate = (total_paid / total_due * 100) if total_due > 0 else 0
    
    # Récupérer les informations de l'école
    school = School.objects.first()
    
    context = {
        'school': school,
        'current_year': current_year,
        'total_students': total_students,
        'total_classes': total_classes,
        'total_paid': total_paid,
        'total_due': total_due,
        'recovery_rate': recovery_rate,
        'generated_at': timezone.now(),
    }
    
    # Générer le PDF
    html_string = render_to_string('finances/performance_report_pdf.html', context)
    pdf = HTML(string=html_string).write_pdf()
    
    # Retourner le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_performance_{current_year.annee}.pdf"'
    return response


# ==================== RAPPORTS PAR ÉTUDIANT ====================

@login_required
def student_report(request, student_id):
    """Rapport financier détaillé par étudiant"""
    student = get_object_or_404(Student, pk=student_id)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Paiements d'inscription
    inscription_payments = InscriptionPayment.objects.filter(
        student=student,
        fee_structure__year=current_year
    ).select_related('fee_structure').order_by('-payment_date')
    
    # Paiements de scolarité
    tuition_payments = TranchePayment.objects.filter(
        student=student,
        tranche__fee_structure__year=current_year
    ).select_related('tranche', 'tranche__fee_structure').order_by('-payment_date')
    
    # Remises
    discounts = FeeDiscount.objects.filter(
        student=student,
        tranche__fee_structure__year=current_year
    ).select_related('tranche').order_by('-granted_at')
    
    # Calculer les montants
    total_inscription_paid = inscription_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_tuition_paid = tuition_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_discounts = discounts.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = total_inscription_paid + total_tuition_paid - total_discounts
    
    # Montants dus
    fee_structure = None
    if student.current_class:
        fee_structure = FeeStructure.objects.filter(
            school_class=student.current_class,
            year=current_year
        ).first()
    
    total_due = 0
    if fee_structure:
        total_due = fee_structure.inscription_fee + fee_structure.tuition_total
    
    remaining = total_due - total_paid
    
    # Prochaines échéances
    upcoming_tranches = []
    if fee_structure:
        today = timezone.now().date()
        upcoming_tranches = FeeTranche.objects.filter(
            fee_structure=fee_structure,
            due_date__gte=today
        ).order_by('due_date')
    
    context = {
        'student': student,
        'current_year': current_year,
        'inscription_payments': inscription_payments,
        'tuition_payments': tuition_payments,
        'discounts': discounts,
        'total_inscription_paid': total_inscription_paid,
        'total_tuition_paid': total_tuition_paid,
        'total_discounts': total_discounts,
        'total_paid': total_paid,
        'total_due': total_due,
        'remaining': remaining,
        'upcoming_tranches': upcoming_tranches,
        'fee_structure': fee_structure,
    }
    
    return render(request, 'finances/student_report.html', context)


@login_required
def export_student_report(request, student_id):
    """Export PDF du rapport étudiant"""
    student = get_object_or_404(Student, pk=student_id)
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les données (même logique que student_report)
    inscription_payments = InscriptionPayment.objects.filter(
        student=student,
        fee_structure__year=current_year
    ).select_related('fee_structure').order_by('-payment_date')
    
    tuition_payments = TranchePayment.objects.filter(
        student=student,
        tranche__fee_structure__year=current_year
    ).select_related('tranche', 'tranche__fee_structure').order_by('-payment_date')
    
    discounts = FeeDiscount.objects.filter(
        student=student,
        tranche__fee_structure__year=current_year
    ).select_related('tranche').order_by('-granted_at')
    
    total_inscription_paid = inscription_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_tuition_paid = tuition_payments.aggregate(total=Sum('amount'))['total'] or 0
    total_discounts = discounts.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = total_inscription_paid + total_tuition_paid - total_discounts
    
    fee_structure = None
    if student.current_class:
        fee_structure = FeeStructure.objects.filter(
            school_class=student.current_class,
            year=current_year
        ).first()
    
    total_due = 0
    if fee_structure:
        total_due = fee_structure.inscription_fee + fee_structure.tuition_total
    
    remaining = total_due - total_paid
    
    # Récupérer les informations de l'école
    school = School.objects.first()
    
    context = {
        'school': school,
        'student': student,
        'current_year': current_year,
        'inscription_payments': inscription_payments,
        'tuition_payments': tuition_payments,
        'discounts': discounts,
        'total_inscription_paid': total_inscription_paid,
        'total_tuition_paid': total_tuition_paid,
        'total_discounts': total_discounts,
        'total_paid': total_paid,
        'total_due': total_due,
        'remaining': remaining,
        'fee_structure': fee_structure,
        'generated_at': timezone.now(),
    }
    
    # Générer le PDF
    html_string = render_to_string('finances/student_report_pdf.html', context)
    pdf = HTML(string=html_string).write_pdf()
    
    # Retourner le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_etudiant_{student.matricule}.pdf"'
    return response 