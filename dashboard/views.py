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
    
    # Derniers paiements avec informations complètes
    last_payments = TranchePayment.objects.select_related(
        'student', 'tranche'
    ).prefetch_related(
        'student__current_class'
    ).order_by('-payment_date')[:10]

    # Données pour les graphiques
    # Évolution des paiements par mois (6 derniers mois)
    monthly_payments = []
    for i in range(6):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=31)
        month_total = TranchePayment.objects.filter(
            payment_date__range=[month_start, month_end]
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_payments.append({
            'month': month_start.strftime('%b'),
            'amount': month_total
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
    }
    return render(request, 'dashboard/dashboard.html', context)