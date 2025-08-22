from django.db import models
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from students.models import Student
from teachers.models import Teacher
from classes.models import SchoolClass
from finances.models import TranchePayment, FeeDiscount, FeeStructure, FeeTranche
from subjects.models import Subject
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
from django.utils import timezone
from school.models import SchoolYear

def get_overdue_students():
    """Récupère les élèves avec retard de paiement depuis l'app finances"""
    current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    if not current_year:
        return []
    
    today = timezone.now().date()
    overdue_students = []
    
    # Récupérer toutes les tranches en retard
    overdue_tranches = FeeTranche.objects.filter(
        due_date__lt=today,
        fee_structure__year=current_year
    ).select_related('fee_structure', 'fee_structure__school_class')
    
    # Pour chaque étudiant actif, vérifier les retards
    active_students = Student.objects.filter(is_active=True).select_related('current_class')
    
    for student in active_students:
        student_overdue = []
        total_overdue = 0
        max_days_overdue = 0
        
        for tranche in overdue_tranches.filter(fee_structure__school_class=student.current_class):
            # Vérifier si l'étudiant a payé cette tranche
            payment = TranchePayment.objects.filter(student=student, tranche=tranche).first()
            paid_amount = payment.amount if payment else 0
            overdue_amount = tranche.amount - paid_amount
            
            if overdue_amount > 0:
                days_overdue = (today - tranche.due_date).days
                max_days_overdue = max(max_days_overdue, days_overdue)
                
                student_overdue.append({
                    'tranche': tranche,
                    'paid_amount': paid_amount,
                    'overdue_amount': overdue_amount,
                    'days_overdue': days_overdue,
                })
                total_overdue += overdue_amount
        
        if student_overdue:
            # Déterminer la sévérité du retard
            if max_days_overdue > 30:
                severity = 'high'
                severity_color = 'red'
            elif max_days_overdue > 7:
                severity = 'medium'
                severity_color = 'yellow'
            else:
                severity = 'low'
                severity_color = 'orange'
            
            overdue_students.append({
                'student': student,
                'overdue_details': student_overdue,
                'total_overdue': total_overdue,
                'max_days_overdue': max_days_overdue,
                'severity': severity,
                'severity_color': severity_color,
            })
    
    # Trier par montant dû décroissant
    overdue_students.sort(key=lambda x: x['total_overdue'], reverse=True)
    
    return overdue_students

@login_required
def dashboard_view(request):
    # Élèves - Statistics détaillées
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    inactive_students = Student.objects.filter(is_active=False).count()
    male_students = Student.objects.filter(gender='M').count()
    female_students = Student.objects.filter(gender='F').count()

    # Répartition par classe - Corrigé avec current_class
    students_by_class = Student.objects.filter(
        current_class__isnull=False
    ).values(
        'current_class__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    # Enseignants
    total_teachers = Teacher.objects.count()
    active_teachers = Teacher.objects.filter(is_active=True).count()

    # Classes et salles
    total_classes = SchoolClass.objects.count()
    total_classrooms = total_classes  # Simplifié car chaque classe est une salle

    # Finances - Calculs améliorés
    # Calcul des frais totaux attendus
    fee_structures = FeeStructure.objects.all()
    total_due = 0
    for fs in fee_structures:
        # Multiplier par le nombre d'élèves dans cette classe et année
        students_count = Student.objects.filter(
            current_class=fs.school_class,
            year=fs.year,
            is_active=True
        ).count()
        total_due += fs.tuition_total * students_count if hasattr(fs, 'tuition_total') else 0
    
    # Si pas de tuition_total, utiliser une méthode alternative
    if total_due == 0:
        total_due = Student.objects.filter(is_active=True).count() * 500000  # Estimation moyenne
    
    # Paiements des tranches
    tranche_payments = TranchePayment.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Paiements d'inscription
    try:
        from finances.models import InscriptionPayment
        inscription_payments = InscriptionPayment.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
    except ImportError:
        inscription_payments = 0
    
    total_paid = tranche_payments + inscription_payments
    total_discount = FeeDiscount.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_remaining = max(0, total_due - total_paid - total_discount)
    
    # Calcul du pourcentage de recouvrement
    recovery_rate = (total_paid / total_due * 100) if total_due > 0 else 0

    # Matières par catégorie
    total_subjects = Subject.objects.count()
    
    # Derniers paiements avec informations complètes - Tous types de paiements
    last_payments = []
    
    # Derniers paiements de tranches
    tranche_payments = TranchePayment.objects.select_related(
        'student', 'tranche'
    ).prefetch_related(
        'student__current_class'
    ).order_by('-payment_date')[:5]
    
    for payment in tranche_payments:
        last_payments.append({
            'student': payment.student,
            'amount': payment.amount,
            'payment_date': payment.payment_date,
            'type': 'Tranche',
            'description': f"Tranche {payment.tranche.number} - {payment.tranche.fee_structure.school_class.name}",
            'mode': payment.mode
        })
    
    # Derniers paiements d'inscription
    try:
        from finances.models import InscriptionPayment
        inscription_payments = InscriptionPayment.objects.select_related(
            'student', 'fee_structure'
        ).prefetch_related(
            'student__current_class'
        ).order_by('-payment_date')[:3]
        
        for payment in inscription_payments:
            last_payments.append({
                'student': payment.student,
                'amount': payment.amount,
                'payment_date': payment.payment_date,
                'type': 'Inscription',
                'description': f"Inscription - {payment.fee_structure.school_class.name}",
                'mode': payment.mode
            })
    except ImportError:
        pass
    
    # Derniers paiements de frais annexes
    try:
        from finances.models import ExtraFeePayment
        extra_fee_payments = ExtraFeePayment.objects.select_related(
            'student', 'extra_fee'
        ).prefetch_related(
            'student__current_class'
        ).order_by('-payment_date')[:3]
        
        for payment in extra_fee_payments:
            last_payments.append({
                'student': payment.student,
                'amount': payment.amount,
                'payment_date': payment.payment_date,
                'type': 'Frais annexe',
                'description': f"{payment.extra_fee.name}",
                'mode': payment.mode
            })
    except ImportError:
        pass
    
    # Trier par date de paiement décroissante et prendre les 10 premiers
    last_payments.sort(key=lambda x: x['payment_date'], reverse=True)
    last_payments = last_payments[:10]

    # Récupérer les élèves avec retard de paiement
    overdue_students = get_overdue_students()
    overdue_count = len(overdue_students)

    # Données pour les graphiques
    # Évolution des paiements par mois (6 derniers mois) - Tous types de paiements
    monthly_payments = []
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=31)
        
        # Paiements des tranches
        tranche_total = TranchePayment.objects.filter(
            payment_date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Paiements d'inscription
        try:
            from finances.models import InscriptionPayment
            inscription_total = InscriptionPayment.objects.filter(
                payment_date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or 0
        except ImportError:
            inscription_total = 0
        
        # Paiements des frais annexes
        try:
            from finances.models import ExtraFeePayment
            extra_fee_total = ExtraFeePayment.objects.filter(
                payment_date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or 0
        except ImportError:
            extra_fee_total = 0
        
        # Total du mois
        month_total = tranche_total + inscription_total + extra_fee_total
        
        monthly_payments.append({
            'month': month_start.strftime('%b'),
            'amount': month_total,
            'tranche': tranche_total,
            'inscription': inscription_total,
            'extra_fees': extra_fee_total
        })
    monthly_payments.reverse()

    # Statistiques de performance
    # Calcul de la moyenne d'occupation des classes
    occupied_classes = SchoolClass.objects.annotate(
        annotated_student_count=Count('students', filter=models.Q(students__is_active=True))
    ).filter(annotated_student_count__gt=0)
    
    avg_occupation = 0
    if occupied_classes.exists():
        total_capacity = sum([cls.capacity for cls in occupied_classes if cls.capacity and cls.capacity > 0])
        total_students_in_classes = sum([cls.annotated_student_count for cls in occupied_classes])
        avg_occupation = (total_students_in_classes / total_capacity * 100) if total_capacity > 0 else 78  # valeur par défaut

    context = {
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'male_students': male_students,
        'female_students': female_students,
        'students_by_class': students_by_class,
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'total_classes': total_classes,
        'total_classrooms': total_classrooms,
        'total_due': total_due,
        'total_paid': total_paid,
        'total_discount': total_discount,
        'total_remaining': total_remaining,
        'total_subjects': total_subjects,
        'last_payments': last_payments,
        'recovery_rate': recovery_rate,
        'monthly_payments': monthly_payments,
        'avg_occupation': avg_occupation,
        # Variables pour le sidebar (compatibilité avec le template)
        'students_count': total_students,
        'teachers_count': total_teachers,
        'classes_count': total_classes,
        # Nouvelles variables pour les retards de paiement
        'overdue_students': overdue_students,
        'overdue_count': overdue_count,
    }
    return render(request, 'dashboard/dashboard.html', context)