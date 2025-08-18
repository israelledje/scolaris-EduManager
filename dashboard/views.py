from django.db import models
from django.shortcuts import render
from students.models import Student
from teachers.models import Teacher
from classes.models import SchoolClass
from finances.models import TranchePayment, FeeDiscount, FeeStructure, FeeTranche
from subjects.models import Subject

def dashboard_view(request):
    # Élèves
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    inactive_students = Student.objects.filter(is_active=False).count()
    male_students = Student.objects.filter(gender='M').count()
    female_students = Student.objects.filter(gender='F').count()

    # Répartition par classe
    students_by_class = Student.objects.values('current_class__name').annotate(count=models.Count('id'))

    # Enseignants
    total_teachers = Teacher.objects.count()
    active_teachers = Teacher.objects.filter(is_active=True).count()

    # Classes et salles
    total_classes = SchoolClass.objects.count()
    total_classrooms = SchoolClass.objects.count()

    # Finances - Calculs optimisés
    fee_structures = FeeStructure.objects.all()
    total_due = sum([fs.tuition_total for fs in fee_structures])
    
    # Paiements des tranches
    tranche_payments = TranchePayment.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Paiements d'inscription (si le modèle existe)
    try:
        from finances.models import InscriptionPayment
        inscription_payments = InscriptionPayment.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    except:
        inscription_payments = 0
    
    total_paid = tranche_payments + inscription_payments
    total_discount = FeeDiscount.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    total_remaining = total_due - total_paid - total_discount
    
    # Calcul du pourcentage de recouvrement
    recovery_rate = (total_paid / total_due * 100) if total_due > 0 else 0

    # Matières
    total_subjects = Subject.objects.count()

    # Derniers paiements
    last_payments = TranchePayment.objects.select_related('student').order_by('-payment_date')[:5]

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
    }
    return render(request, 'dashboard/dashboard.html', context)