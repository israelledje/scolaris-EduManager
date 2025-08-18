from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from functools import wraps
from django.template.loader import render_to_string
from weasyprint import HTML
from django.templatetags.static import static
import json

from .models import (
    Trimester, Evaluation, StudentGrade, Bulletin, BulletinLine, BulletinUtils
)
from students.models import Student
from classes.models import SchoolClass
from subjects.models import Subject
from school.models import SchoolYear, School
from teachers.models import TeachingAssignment

# ==================== VÉRIFICATIONS DROITS ====================

def is_admin_or_direction(user):
    return user.groups.filter(name__in=["ADMIN", "DIRECTION"]).exists() or user.is_superuser

def is_teacher_or_admin(user):
    return user.groups.filter(name__in=["ADMIN", "DIRECTION", "TEACHER"]).exists() or user.is_superuser

def require_school_and_year(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        year = SchoolYear.objects.filter(statut='EN_COURS').first()
        school = School.objects.first()
        if request.user.is_superuser or request.user.groups.filter(name__in=["ADMIN", "DIRECTION"]).exists():
            if not year or not school:
                return redirect('/config-school/')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ==================== DASHBOARD PRINCIPAL ====================

@require_school_and_year
@login_required
def notes_dashboard(request):
    """Dashboard principal de gestion des notes"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    school = School.objects.first()
    
    # Statistiques générales
    total_students = Student.objects.filter(year=year, is_active=True).count()
    total_evaluations = Evaluation.objects.filter(trimester__year=year).count()
    total_grades = StudentGrade.objects.filter(evaluation__trimester__year=year).count()
    
    # Trimestres actifs
    active_trimesters = Trimester.objects.filter(is_active=True, year=year)
    current_trimester = None
    for trimester in active_trimesters:
        if trimester.is_current:
            current_trimester = trimester
            break
    
    # Évaluations ouvertes
    open_evaluations = Evaluation.objects.filter(is_open=True, trimester__year=year)
    
    # Dernières évaluations
    recent_evaluations = Evaluation.objects.filter(trimester__year=year).order_by('-created_at')[:5]
    
    # Statistiques par matière
    subject_stats = []
    subjects = Subject.objects.all()
    for subject in subjects:
        evaluations = Evaluation.objects.filter(subject=subject, trimester__year=year)
        grades = StudentGrade.objects.filter(evaluation__subject=subject, evaluation__trimester__year=year)
        
        avg_score = grades.aggregate(avg=Avg('score'))['avg'] or 0
        success_rate = grades.filter(score__gte=10).count() / grades.count() * 100 if grades.count() > 0 else 0
        
        subject_stats.append({
            'subject': subject,
            'evaluations_count': evaluations.count(),
            'grades_count': grades.count(),
            'avg_score': round(avg_score, 2),
            'success_rate': round(success_rate, 1)
        })
    
    context = {
        'total_students': total_students,
        'total_evaluations': total_evaluations,
        'total_grades': total_grades,
        'active_trimesters': active_trimesters,
        'current_trimester': current_trimester,
        'open_evaluations': open_evaluations,
        'recent_evaluations': recent_evaluations,
        'subject_stats': subject_stats,
    }
    
    return render(request, 'notes/notes_dashboard.html', context)

# ==================== GESTION DES TRIMESTRES ====================

@login_required
@user_passes_test(is_admin_or_direction)
def trimester_list(request):
    """Liste des trimestres"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    trimesters = Trimester.objects.filter(year=year).order_by('trimester')
    
    context = {
        'trimesters': trimesters,
        'year': year,
    }
    return render(request, 'notes/trimester_list.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def trimester_create(request):
    """Créer un trimestre"""
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            trimester_type = request.POST.get('trimester')
            school_year_id = request.POST.get('school_year')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            
            # Validation des données
            if not all([trimester_type, school_year_id, start_date, end_date]):
                messages.error(request, "Tous les champs obligatoires doivent être remplis.")
                return render(request, 'notes/trimester_form.html', {
                    'trimester': None,
                    'school_years': SchoolYear.objects.all().order_by('-annee'),
                    'form_data': request.POST
                })
            
            # Vérifier que l'année scolaire existe
            school_year = get_object_or_404(SchoolYear, id=school_year_id)
            school = School.objects.first()
            
            if not school:
                messages.error(request, "Aucune école configurée. Veuillez configurer l'école d'abord.")
                return render(request, 'notes/trimester_form.html', {
                    'trimester': None,
                    'school_years': SchoolYear.objects.all().order_by('-annee'),
                    'form_data': request.POST
                })
            
            # Vérifier que les dates sont valides
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if start_date >= end_date:
                messages.error(request, "La date de fin doit être postérieure à la date de début.")
                return render(request, 'notes/trimester_form.html', {
                    'trimester': None,
                    'school_years': SchoolYear.objects.all().order_by('-annee'),
                    'form_data': request.POST
                })
            
            # Créer le trimestre
            trimester = Trimester.objects.create(
                trimester=trimester_type,
                year=school_year,
                school=school,
                start_date=start_date,
                end_date=end_date
            )
            
            messages.success(request, f"Le trimestre '{trimester.get_trimester_display()}' a été créé avec succès.")
            return redirect('notes:trimester_list')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du trimestre: {str(e)}")
            return render(request, 'notes/trimester_form.html', {
                'trimester': None,
                'school_years': SchoolYear.objects.all().order_by('-annee'),
                'form_data': request.POST
            })
    
    context = {
        'trimester': None,
        'school_years': SchoolYear.objects.all().order_by('-annee'),
    }
    return render(request, 'notes/trimester_form.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def trimester_detail(request, pk):
    """Détails d'un trimestre"""
    trimester = get_object_or_404(Trimester, pk=pk)
    evaluations = Evaluation.objects.filter(trimester=trimester)
    
    context = {
        'trimester': trimester,
        'evaluations': evaluations,
    }
    return render(request, 'notes/trimester_detail.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def trimester_update(request, pk):
    """Modifier un trimestre"""
    trimester = get_object_or_404(Trimester, pk=pk)
    if request.method == 'POST':
        # Logique de modification
        pass
    
    context = {
        'trimester': trimester,
        'school_years': SchoolYear.objects.all().order_by('-annee'),
    }
    return render(request, 'notes/trimester_form.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def trimester_delete(request, pk):
    """Supprimer un trimestre"""
    trimester = get_object_or_404(Trimester, pk=pk)
    if request.method == 'POST':
        trimester.delete()
        messages.success(request, "Trimestre supprimé avec succès.")
        return redirect('notes:trimester_list')
    return render(request, 'notes/trimester_delete_confirm.html', {'trimester': trimester})

# ==================== GESTION DES ÉVALUATIONS ====================

@login_required
@user_passes_test(is_teacher_or_admin)
def evaluation_list(request):
    """Liste des classes avec évaluations"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer toutes les classes qui ont des évaluations
    classes_with_evaluations = SchoolClass.objects.filter(
        year=year,
        evaluations__trimester__year=year
    ).distinct().prefetch_related('students', 'evaluations', 'evaluations__grades')
    
    # Filtres
    class_filter = request.GET.get('class')
    if class_filter:
        classes_with_evaluations = classes_with_evaluations.filter(id=class_filter)
    
    # Calculer les statistiques pour chaque classe
    classes_data = []
    for school_class in classes_with_evaluations:
        evaluations = school_class.evaluations.filter(trimester__year=year)
        total_students = school_class.students.count()
        total_evaluations = evaluations.count()
        total_grades = sum(evaluation.grades.count() for evaluation in evaluations)
        completed_evaluations = sum(1 for evaluation in evaluations if evaluation.grades.count() >= total_students)
        open_evaluations = evaluations.filter(is_open=True).count()
        
        # Vérifier si on peut générer des bulletins
        can_generate_bulletins = False
        ready_trimester = None
        for trimester in Trimester.objects.filter(year=year):
            trimester_evaluations = evaluations.filter(trimester=trimester)
            if trimester_evaluations.exists():
                trimester_completed = sum(1 for e in trimester_evaluations if e.grades.count() >= total_students)
                if trimester_completed == trimester_evaluations.count():
                    can_generate_bulletins = True
                    ready_trimester = trimester
                    break
        
        classes_data.append({
            'class': school_class,
            'total_students': total_students,
            'total_evaluations': total_evaluations,
            'total_grades': total_grades,
            'completed_evaluations': completed_evaluations,
            'open_evaluations': open_evaluations,
            'can_generate_bulletins': can_generate_bulletins,
            'ready_trimester': ready_trimester,
        })
    
    # Statistiques globales
    total_classes = len(classes_data)
    total_evaluations = sum(data['total_evaluations'] for data in classes_data)
    total_grades = sum(data['total_grades'] for data in classes_data)
    total_open_evaluations = sum(data['open_evaluations'] for data in classes_data)
    
    # Pagination
    paginator = Paginator(classes_data, 12)  # 12 classes par page
    page_number = request.GET.get('page')
    classes_page = paginator.get_page(page_number)
    
    context = {
        'classes_data': classes_page,
        'classes': SchoolClass.objects.filter(year=year),
        'selected_class': class_filter,
        'total_classes': total_classes,
        'total_evaluations': total_evaluations,
        'total_grades': total_grades,
        'total_open_evaluations': total_open_evaluations,
    }
    return render(request, 'notes/evaluation_list.html', context)

@login_required
@user_passes_test(is_teacher_or_admin)
def evaluation_create(request):
    """Créer une évaluation pour toutes les matières d'une classe"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            eval_type = request.POST.get('eval_type')
            trimester_id = request.POST.get('trimester')
            school_class_id = request.POST.get('school_class')
            eval_date = request.POST.get('eval_date')
            max_score = request.POST.get('max_score', 20)
            duration = request.POST.get('duration', 60)
            instructions = request.POST.get('instructions', '')
            is_open = request.POST.get('is_open') == 'on'
            
            # Validation des données
            if not all([eval_type, trimester_id, school_class_id, eval_date]):
                messages.error(request, "Tous les champs obligatoires doivent être remplis.")
                raise ValueError("Données manquantes")
            
            # Récupération des objets
            trimester = get_object_or_404(Trimester, id=trimester_id)
            school_class = get_object_or_404(SchoolClass, id=school_class_id)
            
            # Récupération de toutes les matières enseignées dans cette classe
            teaching_assignments = TeachingAssignment.objects.filter(
                school_class=school_class,
                year=year
            ).select_related('subject')
            
            if not teaching_assignments.exists():
                messages.error(request, f"Aucune matière n'est enseignée dans la classe {school_class.name}.")
                raise ValueError("Aucune matière enseignée")
            
            # Création d'une évaluation pour chaque matière
            created_evaluations = []
            for assignment in teaching_assignments:
                # Vérification si l'évaluation existe déjà
                existing_evaluation = Evaluation.objects.filter(
                    eval_type=eval_type,
                    trimester=trimester,
                    subject=assignment.subject,
                    school_class=school_class
                ).first()
                
                if existing_evaluation:
                    messages.warning(request, f"L'évaluation {eval_type} pour {assignment.subject.name} existe déjà.")
                    continue
                
                # Création de l'évaluation
                evaluation = Evaluation.objects.create(
                    eval_type=eval_type,
                    trimester=trimester,
                    subject=assignment.subject,
                    school_class=school_class,
                    max_score=max_score,
                    coefficient=assignment.coefficient,  # Utilisation du coefficient de l'assignation
                    eval_date=eval_date,
                    duration=duration,
                    instructions=instructions,
                    is_open=is_open,
                    created_by=request.user
                )
                created_evaluations.append(evaluation)
            
            if created_evaluations:
                messages.success(
                    request, 
                    f"{len(created_evaluations)} évaluation(s) créée(s) avec succès pour la classe {school_class.name}."
                )
                return redirect('notes:evaluation_list')
            else:
                messages.warning(request, "Aucune nouvelle évaluation n'a été créée.")
                
        except ValueError as e:
            # Erreur de validation, on continue pour afficher le formulaire avec les erreurs
            pass
        except Exception as e:
            messages.error(request, f"Erreur lors de la création des évaluations : {str(e)}")
    
    context = {
        'evaluation': None,
        'subjects': Subject.objects.all(),
        'classes': SchoolClass.objects.filter(year=year),
        'trimesters': Trimester.objects.filter(year=year, is_active=True),
        'year': year,
    }
    return render(request, 'notes/evaluation_form.html', context)

@login_required
@user_passes_test(is_teacher_or_admin)
def evaluation_update(request, pk):
    """Modifier une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=pk)
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    if request.method == 'POST':
        # Logique de modification
        pass
    
    context = {
        'evaluation': evaluation,
        'subjects': Subject.objects.all(),
        'classes': SchoolClass.objects.filter(year=year),
        'trimesters': Trimester.objects.filter(year=year, is_active=True),
        'year': year,
    }
    return render(request, 'notes/evaluation_form.html', context)

@login_required
@user_passes_test(is_teacher_or_admin)
def evaluation_delete(request, pk):
    """Supprimer une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=pk)
    if request.method == 'POST':
        evaluation.delete()
        messages.success(request, "Évaluation supprimée avec succès.")
        return redirect('notes:evaluation_list')
    return render(request, 'notes/evaluation_delete_confirm.html', {'evaluation': evaluation})

@login_required
@user_passes_test(is_teacher_or_admin)
def evaluation_detail(request, pk):
    """Détails d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=pk)
    grades = StudentGrade.objects.filter(evaluation=evaluation).select_related('student')
    
    # Statistiques
    stats = {
        'total_students': grades.count(),
        'average_score': grades.aggregate(avg=Avg('score'))['avg'] or 0,
        'success_rate': grades.filter(score__gte=10).count() / grades.count() * 100 if grades.count() > 0 else 0,
        'highest_score': grades.aggregate(max=models.Max('score'))['max'] or 0,
        'lowest_score': grades.aggregate(min=models.Min('score'))['min'] or 0,
    }
    
    context = {
        'evaluation': evaluation,
        'grades': grades,
        'stats': stats,
    }
    return render(request, 'notes/evaluation_detail.html', context)

@login_required
@user_passes_test(is_teacher_or_admin)
def evaluation_close(request, pk):
    """Clôturer une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=pk)
    if request.method == 'POST':
        evaluation.close_evaluation()
        messages.success(request, f"L'évaluation {evaluation} a été clôturée avec succès.")
        return redirect('notes:evaluation_detail', pk=pk)
    
    return render(request, 'notes/evaluation_close_confirm.html', {'evaluation': evaluation})

# ==================== SAISIE DES NOTES ====================

@login_required
@user_passes_test(is_teacher_or_admin)
def grade_entry(request, evaluation_id):
    """Interface de saisie des notes"""
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    
    if not evaluation.is_open:
        messages.error(request, "Cette évaluation est fermée pour la saisie.")
        return redirect('notes:evaluation_detail', pk=evaluation_id)
    
    # Récupérer les étudiants de la classe
    students = Student.objects.filter(
        current_class=evaluation.school_class,
        year=evaluation.trimester.year,
        is_active=True
    ).order_by('last_name', 'first_name')
    
    # Récupérer les notes existantes
    existing_grades = StudentGrade.objects.filter(evaluation=evaluation)
    grades_dict = {grade.student_id: grade for grade in existing_grades}
    
    context = {
        'evaluation': evaluation,
        'students': students,
        'grades_dict': grades_dict,
    }
    return render(request, 'notes/grade_entry.html', context)

@login_required
@user_passes_test(is_teacher_or_admin)
def bulk_grade_entry(request, evaluation_id):
    """Saisie en lot des notes"""
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    
    if request.method == 'POST':
        # Traitement de la saisie en lot
        pass
    
    students = Student.objects.filter(
        current_class=evaluation.school_class,
        year=evaluation.trimester.year,
        is_active=True
    ).order_by('last_name', 'first_name')
    
    context = {
        'evaluation': evaluation,
        'students': students,
    }
    return render(request, 'notes/bulk_grade_entry.html', context)

@login_required
@user_passes_test(is_teacher_or_admin)
def grade_list(request):
    """Liste des notes"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    grades = StudentGrade.objects.filter(evaluation__trimester__year=year).select_related(
        'student', 'evaluation', 'evaluation__subject', 'evaluation__school_class'
    ).order_by('-graded_at')
    
    # Pagination
    paginator = Paginator(grades, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'notes/grade_list.html', context)

@login_required
@user_passes_test(is_teacher_or_admin)
def grade_update(request, pk):
    """Modifier une note"""
    grade = get_object_or_404(StudentGrade, pk=pk)
    if request.method == 'POST':
        # Logique de modification
        pass
    return render(request, 'notes/grade_form.html', {'grade': grade})

@login_required
@user_passes_test(is_teacher_or_admin)
def grade_delete(request, pk):
    """Supprimer une note"""
    grade = get_object_or_404(StudentGrade, pk=pk)
    if request.method == 'POST':
        grade.delete()
        messages.success(request, "Note supprimée avec succès.")
        return redirect('notes:evaluation_detail', pk=grade.evaluation.pk)
    return render(request, 'notes/grade_delete_confirm.html', {'grade': grade})

# ==================== GESTION DES BULLETINS ====================

@login_required
@user_passes_test(is_admin_or_direction)
def bulletin_list(request):
    """Liste des bulletins"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    bulletins = Bulletin.objects.filter(trimester__year=year).select_related(
        'student', 'trimester'
    ).order_by('-generated_at')
    
    # Filtres
    trimester_filter = request.GET.get('trimester')
    class_filter = request.GET.get('class')
    status_filter = request.GET.get('status')
    
    if trimester_filter:
        bulletins = bulletins.filter(trimester_id=trimester_filter)
    if class_filter:
        bulletins = bulletins.filter(student__school_class_id=class_filter)
    if status_filter == 'approved':
        bulletins = bulletins.filter(is_approved=True)
    elif status_filter == 'draft':
        bulletins = bulletins.filter(is_approved=False)
    
    # Pagination
    paginator = Paginator(bulletins, 25)
    page_number = request.GET.get('page')
    bulletins = paginator.get_page(page_number)
    
    # Trimestre en cours
    current_trimester = None
    active_trimesters = Trimester.objects.filter(is_active=True, year=year)
    for trimester in active_trimesters:
        if trimester.is_current:
            current_trimester = trimester
            break
    
    # Si aucun trimestre n'est marqué comme courant, prendre le premier trimestre actif
    if current_trimester is None and active_trimesters.exists():
        current_trimester = active_trimesters.first()
    
    context = {
        'bulletins': bulletins,
        'trimesters': Trimester.objects.filter(year=year),
        'classes': SchoolClass.objects.filter(year=year),
        'current_trimester': current_trimester,
        'selected_trimester': trimester_filter,
        'selected_class': class_filter,
        'status_filter': status_filter,
    }
    return render(request, 'notes/bulletin_list.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def generate_bulletins(request, trimester_id):
    """Générer les bulletins pour un trimestre"""
    trimester = get_object_or_404(Trimester, pk=trimester_id)
    
    if request.method == 'POST':
        try:
            count = BulletinUtils.generate_bulletins_for_trimester(trimester_id)
            messages.success(request, f"{count} bulletins ont été générés avec succès.")
            return redirect('notes:bulletin_list')
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération des bulletins: {str(e)}")
    
    context = {
        'trimester': trimester,
    }
    return render(request, 'notes/generate_bulletins_confirm.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def bulletin_detail(request, pk):
    """Détails d'un bulletin"""
    bulletin = get_object_or_404(Bulletin, pk=pk)
    
    # Récupérer les informations de l'école
    try:
        school = School.objects.first()
        school_name = school.nom if school else "Établissement Scolaire"
        
        # Récupérer l'en-tête de document de l'école
        school_logo_url = request.build_absolute_uri(static('images/logo.png'))  # Fallback par défaut
        if school:
            document_header = school.get_active_header()
            if document_header and document_header.logo:
                try:
                    school_logo_url = request.build_absolute_uri(document_header.logo.url)
                except Exception:
                    pass  # Garder le fallback si erreur
    except Exception:
        school_name = "Établissement Scolaire"
        school_logo_url = request.build_absolute_uri(static('images/logo.png'))
    
    # Récupérer les notes détaillées pour chaque matière
    bulletin_lines_with_grades = []
    
    for line in bulletin.lines.all():
        # Récupérer les évaluations EVAL1 et EVAL2 pour cette matière dans ce trimestre
        evaluations = Evaluation.objects.filter(
            trimester=bulletin.trimester,
            subject=line.subject,
            school_class=bulletin.student.current_class,
            eval_type__in=['EVAL1', 'EVAL2']
        ).order_by('eval_type')
        
        # Récupérer le coefficient et l'enseignant depuis TeachingAssignment
        teaching_assignment = TeachingAssignment.objects.filter(
            subject=line.subject,
            school_class=bulletin.student.current_class,
            year=bulletin.trimester.year
        ).select_related('teacher').first()
        
        real_coefficient = teaching_assignment.coefficient if teaching_assignment else line.coefficient
        teacher_name = f"{teaching_assignment.teacher.last_name.upper()} {teaching_assignment.teacher.first_name}" if teaching_assignment and teaching_assignment.teacher else "Non assigné"
        
        # Récupérer les notes de l'élève pour ces évaluations
        grades = StudentGrade.objects.filter(
            student=bulletin.student,
            evaluation__in=evaluations
        ).select_related('evaluation')
        
        # Organiser les notes par type d'évaluation
        eval1_score = None
        eval2_score = None
        
        for grade in grades:
            if grade.evaluation.eval_type == 'EVAL1':
                eval1_score = grade.score
            elif grade.evaluation.eval_type == 'EVAL2':
                eval2_score = grade.score
        
        # Calculer les statistiques de classe pour cette matière
        all_class_grades = StudentGrade.objects.filter(
            evaluation__trimester=bulletin.trimester,
            evaluation__subject=line.subject,
            evaluation__school_class=bulletin.student.current_class
        ).select_related('student')
        
        class_average = 0
        class_highest = 0
        class_lowest = 20
        class_count = 0
        
        if all_class_grades.exists():
            scores = [grade.score for grade in all_class_grades]
            class_average = sum(scores) / len(scores)
            class_highest = max(scores)
            class_lowest = min(scores)
            class_count = len(set(grade.student for grade in all_class_grades))
        
        # Calculer le rang de l'élève dans cette matière
        student_rank = 1
        if all_class_grades.exists():
            # Grouper les notes par élève
            student_scores = {}
            for grade in all_class_grades:
                if grade.student not in student_scores:
                    student_scores[grade.student] = []
                student_scores[grade.student].append(grade.score)
            
            # Calculer la moyenne par élève pour cette matière
            student_averages = {}
            for student, scores in student_scores.items():
                student_averages[student] = sum(scores) / len(scores)
            
            # Trier par moyenne décroissante
            sorted_students = sorted(student_averages.items(), key=lambda x: x[1], reverse=True)
            
            # Trouver le rang de l'élève
            for rank, (student, avg) in enumerate(sorted_students, 1):
                if student == bulletin.student:
                    student_rank = rank
                    break
        
        # Calculer le pourcentage par rapport à la moyenne de classe (limité à 100%)
        percentage = 0
        if class_average > 0:
            percent = (float(line.average) / float(class_average)) * 100
            percentage = min(percent, 100)
        
        # Calculer la cote basée sur la moyenne
        average_percentage = (float(line.average) / 20) * 100
        if average_percentage >= 90:
            cote = "A+"
            appreciation = "Expert"
        elif average_percentage >= 70:
            cote = "A"
            appreciation = "Acquis"
        elif average_percentage >= 55:
            cote = "B"
            appreciation = "En cours d'acquisition"
        elif average_percentage >= 30:
            cote = "C"
            appreciation = "Compétence moyennement acquise (CMA)"
        else:
            cote = "D"
            appreciation = "Non acquis"
        
        # Ajouter les données enrichies
        line_data = {
            'line': line,
            'eval1_score': eval1_score,
            'eval2_score': eval2_score,
            'coefficient': real_coefficient,
            'teacher_name': teacher_name,
            'class_average': class_average,
            'class_highest': class_highest,
            'class_lowest': class_lowest,
            'class_count': class_count,
            'rank': student_rank,
            'percentage': percentage,
            'cote': cote,
            'appreciation': appreciation
        }
        
        bulletin_lines_with_grades.append(line_data)
    
    # Calculer les totaux par groupe
    group1_lines = [data for data in bulletin_lines_with_grades if data['line'].subject.group == 1]
    group2_lines = [data for data in bulletin_lines_with_grades if data['line'].subject.group == 2]
    
    group1_average = 0
    group1_coefficient = 0
    group1_points = 0
    
    if group1_lines:
        total_points = sum(float(line['line'].total_points) for line in group1_lines)
        total_coefs = sum(float(line['coefficient']) for line in group1_lines)
        group1_points = total_points
        group1_coefficient = total_coefs
        group1_average = total_points / total_coefs if total_coefs > 0 else 0
    
    group2_average = 0
    group2_coefficient = 0
    group2_points = 0
    
    if group2_lines:
        total_points = sum(float(line['line'].total_points) for line in group2_lines)
        total_coefs = sum(float(line['coefficient']) for line in group2_lines)
        group2_points = total_points
        group2_coefficient = total_coefs
        group2_average = total_points / total_coefs if total_coefs > 0 else 0
    
    # Récupérer les moyennes précédentes
    previous_bulletins = Bulletin.objects.filter(
        student=bulletin.student,
        trimester__year=bulletin.trimester.year,
        trimester__trimester__lt=bulletin.trimester.trimester
    ).order_by('trimester__trimester')
    
    previous_averages = []
    for prev_bulletin in previous_bulletins:
        previous_averages.append({
            'trimester': prev_bulletin.trimester.get_trimester_display(),
            'average': prev_bulletin.student_average,
            'rank': prev_bulletin.student_rank
        })
    
    # Calculer les statistiques de classe
    all_class_bulletins = Bulletin.objects.filter(
        trimester=bulletin.trimester,
        student__current_class=bulletin.student.current_class
    ).order_by('student_average')
    
    class_highest = 0
    class_lowest = 20
    standard_deviation = 0
    
    if all_class_bulletins.exists():
        averages = [float(b.student_average) for b in all_class_bulletins]
        class_highest = max(averages)
        class_lowest = min(averages)
        
        # Calculer l'écart type
        mean = sum(averages) / len(averages)
        variance = sum((x - mean) ** 2 for x in averages) / len(averages)
        standard_deviation = variance ** 0.5
    
    context = {
        'bulletin': bulletin,
        'school_name': school_name,
        'school_logo': school_logo_url,
        'bulletin_lines_with_grades': bulletin_lines_with_grades,
        'group1_average': group1_average,
        'group1_coefficient': group1_coefficient,
        'group1_points': group1_points,
        'group2_average': group2_average,
        'group2_coefficient': group2_coefficient,
        'group2_points': group2_points,
        'previous_averages': previous_averages,
        'class_highest': class_highest,
        'class_lowest': class_lowest,
        'standard_deviation': standard_deviation,
        # Données factices pour les champs non implémentés
        'conduct': {},
        'work_appreciation': {},
        'supervisor_observations': '',
        'parent_observations': '',
        'main_teacher_visa': '',
        'progress_status': 'En cours'
    }
    
    return render(request, 'notes/bulletin_detail.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def bulletin_pdf(request, pk):
    """Générer le PDF d'un bulletin"""
    bulletin = get_object_or_404(Bulletin, pk=pk)

    # Récupérer les informations de l'école et le logo
    try:
        school = School.objects.first()
        school_name = school.nom if school else "Établissement Scolaire"
        school_address = school.adresse if school else "Adresse de l'établissement"
        school_phone = school.telephone if school else "Téléphone de l'établissement"
        if school and getattr(school, 'logo', None):
            school_logo_url = request.build_absolute_uri(school.logo.url)
        else:
            school_logo_url = request.build_absolute_uri(static('images/logo.png'))
        school_signature_url = request.build_absolute_uri(school.signature.url) if school and getattr(school, 'signature', None) else None
    except Exception:
        school_name = "Établissement Scolaire"
        school_address = "Adresse de l'établissement"
        school_phone = "Téléphone de l'établissement"
        school_logo_url = request.build_absolute_uri(static('images/logo.png'))
        school_signature_url = None

    # Reprendre les mêmes calculs que la page détail pour garantir l'identité des données
    bulletin_lines_with_grades = []
    for line in bulletin.lines.all():
        evaluations = Evaluation.objects.filter(
            trimester=bulletin.trimester,
            subject=line.subject,
            school_class=bulletin.student.current_class,
            eval_type__in=['EVAL1', 'EVAL2']
        ).order_by('eval_type')

        teaching_assignment = TeachingAssignment.objects.filter(
            subject=line.subject,
            school_class=bulletin.student.current_class,
            year=bulletin.trimester.year
        ).select_related('teacher').first()

        real_coefficient = teaching_assignment.coefficient if teaching_assignment else line.coefficient
        teacher_name = f"{teaching_assignment.teacher.last_name.upper()} {teaching_assignment.teacher.first_name}" if teaching_assignment and teaching_assignment.teacher else "Non assigné"

        grades = StudentGrade.objects.filter(
            student=bulletin.student,
            evaluation__in=evaluations
        ).select_related('evaluation')

        eval1_score = None
        eval2_score = None
        for grade in grades:
            if grade.evaluation.eval_type == 'EVAL1':
                eval1_score = grade.score
            elif grade.evaluation.eval_type == 'EVAL2':
                eval2_score = grade.score

        all_class_grades = StudentGrade.objects.filter(
            evaluation__trimester=bulletin.trimester,
            evaluation__subject=line.subject,
            evaluation__school_class=bulletin.student.current_class
        ).select_related('student')

        class_average = 0
        class_highest = 0
        class_lowest = 20
        class_count = 0
        if all_class_grades.exists():
            scores = [grade.score for grade in all_class_grades]
            class_average = sum(scores) / len(scores)
            class_highest = max(scores)
            class_lowest = min(scores)
            class_count = len(set(grade.student for grade in all_class_grades))

        student_rank = 1
        if all_class_grades.exists():
            student_scores = {}
            for grade in all_class_grades:
                student_scores.setdefault(grade.student, []).append(grade.score)
            student_averages = {student: sum(scores) / len(scores) for student, scores in student_scores.items()}
            sorted_students = sorted(student_averages.items(), key=lambda x: x[1], reverse=True)
            for rank, (student, avg) in enumerate(sorted_students, 1):
                if student == bulletin.student:
                    student_rank = rank
                    break

        percentage = 0
        if class_average > 0:
            percent = (float(line.average) / float(class_average)) * 100
            percentage = min(percent, 100)

        average_percentage = (float(line.average) / 20) * 100
        if average_percentage >= 90:
            cote = "A+"; appreciation = "Expert"
        elif average_percentage >= 70:
            cote = "A"; appreciation = "Acquis"
        elif average_percentage >= 55:
            cote = "B"; appreciation = "En cours d'acquisition"
        elif average_percentage >= 30:
            cote = "C"; appreciation = "Compétence moyennement acquise (CMA)"
        else:
            cote = "D"; appreciation = "Non acquis"

        line_data = {
            'line': line,
            'eval1_score': eval1_score,
            'eval2_score': eval2_score,
            'coefficient': real_coefficient,
            'teacher_name': teacher_name,
            'class_average': class_average,
            'class_highest': class_highest,
            'class_lowest': class_lowest,
            'class_count': class_count,
            'rank': student_rank,
            'percentage': percentage,
            'cote': cote,
            'appreciation': appreciation
        }
        bulletin_lines_with_grades.append(line_data)

    group1_lines = [d for d in bulletin_lines_with_grades if d['line'].subject.group == 1]
    group2_lines = [d for d in bulletin_lines_with_grades if d['line'].subject.group == 2]
    group1_points = sum(float(l['line'].total_points) for l in group1_lines) if group1_lines else 0
    group1_coefficient = sum(float(l['coefficient']) for l in group1_lines) if group1_lines else 0
    group1_average = (group1_points / group1_coefficient) if group1_coefficient > 0 else 0
    group2_points = sum(float(l['line'].total_points) for l in group2_lines) if group2_lines else 0
    group2_coefficient = sum(float(l['coefficient']) for l in group2_lines) if group2_lines else 0
    group2_average = (group2_points / group2_coefficient) if group2_coefficient > 0 else 0

    previous_bulletins = Bulletin.objects.filter(
        student=bulletin.student,
        trimester__year=bulletin.trimester.year,
        trimester__trimester__lt=bulletin.trimester.trimester
    ).order_by('trimester__trimester')
    previous_averages = [
        {'trimester': b.trimester.get_trimester_display(), 'average': b.student_average, 'rank': b.student_rank}
        for b in previous_bulletins
    ]
    all_class_bulletins = Bulletin.objects.filter(
        trimester=bulletin.trimester,
        student__current_class=bulletin.student.current_class
    ).order_by('student_average')
    class_highest = max([float(b.student_average) for b in all_class_bulletins]) if all_class_bulletins.exists() else 0
    class_lowest = min([float(b.student_average) for b in all_class_bulletins]) if all_class_bulletins.exists() else 20
    standard_deviation = 0
    if all_class_bulletins.exists():
        averages = [float(b.student_average) for b in all_class_bulletins]
        mean = sum(averages) / len(averages)
        variance = sum((x - mean) ** 2 for x in averages) / len(averages)
        standard_deviation = variance ** 0.5

    context = {
        'bulletin': bulletin,
        'school_name': school_name,
        'school_address': school_address,
        'school_phone': school_phone,
        'school_logo': school_logo_url,
        'school_signature': school_signature_url,
        'bulletin_lines_with_grades': bulletin_lines_with_grades,
        'group1_average': group1_average,
        'group1_coefficient': group1_coefficient,
        'group1_points': group1_points,
        'group2_average': group2_average,
        'group2_coefficient': group2_coefficient,
        'group2_points': group2_points,
        'previous_averages': previous_averages,
        'class_highest': class_highest,
        'class_lowest': class_lowest,
        'standard_deviation': standard_deviation,
        'conduct': {},
        'work_appreciation': {},
        'supervisor_observations': '',
        'parent_observations': '',
        'main_teacher_visa': '',
        'progress_status': 'En cours',
    }

    # Générer le PDF avec base_url pour permettre la résolution des ressources statiques
    html_string = render_to_string('notes/bulletin_pdf.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bulletin_{bulletin.student.matricule}_{bulletin.trimester.trimester}.pdf"'
    return response

@login_required
@user_passes_test(is_admin_or_direction)
def bulletin_approve(request, pk):
    """Approuver un bulletin"""
    bulletin = get_object_or_404(Bulletin, pk=pk)
    
    if request.method == 'POST':
        bulletin.is_approved = True
        bulletin.approved_at = timezone.now()
        bulletin.approved_by = request.user
        bulletin.save()
        messages.success(request, "Le bulletin a été approuvé avec succès.")
        return redirect('notes:bulletin_detail', pk=pk)
    
    return render(request, 'notes/bulletin_approve_confirm.html', {'bulletin': bulletin})

@login_required
@user_passes_test(is_admin_or_direction)
def bulletin_pdf_batch(request):
    """Générer des bulletins en lot en PDF"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    if request.method == 'POST':
        try:
            # Récupérer les paramètres
            trimester_id = request.POST.get('trimester')
            class_id = request.POST.get('class')
            include_approved = request.POST.get('include_approved') == 'on'
            include_draft = request.POST.get('include_draft') == 'on'
            
            # Filtrer les bulletins
            bulletins = Bulletin.objects.filter(trimester__year=year)
            
            if trimester_id:
                bulletins = bulletins.filter(trimester_id=trimester_id)
            
            if class_id:
                bulletins = bulletins.filter(student__current_class_id=class_id)
            
            # Filtrer par statut
            if include_approved and not include_draft:
                bulletins = bulletins.filter(is_approved=True)
            elif include_draft and not include_approved:
                bulletins = bulletins.filter(is_approved=False)
            elif not include_approved and not include_draft:
                # Si aucun statut sélectionné, inclure tous
                pass
            
            if not bulletins.exists():
                messages.error(request, "Aucun bulletin trouvé avec les critères sélectionnés.")
                return redirect('notes:bulletin_list')
            
            # Récupérer les informations de l'école
            try:
                school = School.objects.first()
                school_name = school.nom if school else "Établissement Scolaire"
                school_address = school.adresse if school else "Adresse de l'établissement"
                school_phone = school.telephone if school else "Téléphone de l'établissement"
            except:
                school_name = "Établissement Scolaire"
                school_address = "Adresse de l'établissement"
                school_phone = "Téléphone de l'établissement"
            
            # Préparer le contexte pour chaque bulletin
            bulletins_data = []
            for bulletin in bulletins.select_related('student', 'trimester', 'student__current_class'):
                # Récupérer les données enrichies pour chaque bulletin
                bulletin_lines_with_grades = []
                
                for line in bulletin.lines.all():
                    # Récupérer les évaluations EVAL1 et EVAL2
                    evaluations = Evaluation.objects.filter(
                        trimester=bulletin.trimester,
                        subject=line.subject,
                        school_class=bulletin.student.current_class,
                        eval_type__in=['EVAL1', 'EVAL2']
                    ).order_by('eval_type')
                    
                    # Récupérer le coefficient et l'enseignant
                    teaching_assignment = TeachingAssignment.objects.filter(
                        subject=line.subject,
                        school_class=bulletin.student.current_class,
                        year=bulletin.trimester.year
                    ).select_related('teacher').first()
                    
                    real_coefficient = teaching_assignment.coefficient if teaching_assignment else line.coefficient
                    teacher_name = f"{teaching_assignment.teacher.last_name.upper()} {teaching_assignment.teacher.first_name}" if teaching_assignment and teaching_assignment.teacher else "Non assigné"
                    
                    # Récupérer les notes
                    grades = StudentGrade.objects.filter(
                        student=bulletin.student,
                        evaluation__in=evaluations
                    ).select_related('evaluation')
                    
                    eval1_score = None
                    eval2_score = None
                    
                    for grade in grades:
                        if grade.evaluation.eval_type == 'EVAL1':
                            eval1_score = grade.score
                        elif grade.evaluation.eval_type == 'EVAL2':
                            eval2_score = grade.score
                    
                    # Calculer les statistiques de classe
                    all_class_grades = StudentGrade.objects.filter(
                        evaluation__trimester=bulletin.trimester,
                        evaluation__subject=line.subject,
                        evaluation__school_class=bulletin.student.current_class,
                        evaluation__eval_type__in=['EVAL1', 'EVAL2']
                    ).select_related('student')
                    
                    class_average = 0
                    if all_class_grades.exists():
                        scores = [grade.score for grade in all_class_grades]
                        class_average = sum(scores) / len(scores)
                    
                    # Calculer le rang
                    student_rank = 1
                    if all_class_grades.exists():
                        # Grouper les notes par élève
                        student_scores = {}
                        for grade in all_class_grades:
                            if grade.student not in student_scores:
                                student_scores[grade.student] = []
                            student_scores[grade.student].append(grade.score)
                        
                        # Calculer la moyenne par élève pour cette matière
                        student_averages = {}
                        for student, scores in student_scores.items():
                            student_averages[student] = sum(scores) / len(scores)
                        
                        # Trier par moyenne décroissante
                        sorted_students = sorted(student_averages.items(), key=lambda x: x[1], reverse=True)
                        
                        # Trouver le rang de l'élève
                        for rank, (student, avg) in enumerate(sorted_students, 1):
                            if student == bulletin.student:
                                student_rank = rank
                                break
                    
                    # Calculer le pourcentage (limité à 100%)
                    percentage = 0
                    if class_average > 0:
                        percent = (float(line.average) / float(class_average)) * 100
                        percentage = min(percent, 100)
                    
                    # Calculer la cote basée sur la moyenne
                    average_percentage = (float(line.average) / 20) * 100
                    if average_percentage >= 90:
                        cote = "A+"
                        appreciation = "Expert"
                    elif average_percentage >= 70:
                        cote = "A"
                        appreciation = "Acquis"
                    elif average_percentage >= 55:
                        cote = "B"
                        appreciation = "En cours d'acquisition"
                    elif average_percentage >= 30:
                        cote = "C"
                        appreciation = "Compétence moyennement acquise (CMA)"
                    else:
                        cote = "D"
                        appreciation = "Non acquis"
                    
                    line_data = {
                        'line': line,
                        'eval1_score': eval1_score,
                        'eval2_score': eval2_score,
                        'coefficient': real_coefficient,
                        'teacher_name': teacher_name,
                        'class_average': class_average,
                        'rank': student_rank,
                        'percentage': percentage,
                        'cote': cote,
                        'appreciation': appreciation
                    }
                    
                    bulletin_lines_with_grades.append(line_data)
                
                # Calculer les totaux par groupe
                group1_lines = [data for data in bulletin_lines_with_grades if data['line'].subject.group == 1]
                group2_lines = [data for data in bulletin_lines_with_grades if data['line'].subject.group == 2]
                
                group1_average = 0
                group1_coefficient = 0
                group1_points = 0
                
                if group1_lines:
                    total_points = sum(float(line['line'].total_points) for line in group1_lines)
                    total_coefs = sum(float(line['coefficient']) for line in group1_lines)
                    group1_points = total_points
                    group1_coefficient = total_coefs
                    group1_average = total_points / total_coefs if total_coefs > 0 else 0
                
                group2_average = 0
                group2_coefficient = 0
                group2_points = 0
                
                if group2_lines:
                    total_points = sum(float(line['line'].total_points) for line in group2_lines)
                    total_coefs = sum(float(line['coefficient']) for line in group2_lines)
                    group2_points = total_points
                    group2_coefficient = total_coefs
                    group2_average = total_points / total_coefs if total_coefs > 0 else 0
                
                # Récupérer les moyennes précédentes
                previous_bulletins = Bulletin.objects.filter(
                    student=bulletin.student,
                    trimester__year=bulletin.trimester.year,
                    trimester__trimester__lt=bulletin.trimester.trimester
                ).order_by('trimester__trimester')
                
                previous_averages = []
                for prev_bulletin in previous_bulletins:
                    previous_averages.append({
                        'trimester': prev_bulletin.trimester.get_trimester_display(),
                        'average': prev_bulletin.student_average,
                        'rank': prev_bulletin.student_rank
                    })
                
                # Calculer les statistiques de classe
                all_class_bulletins = Bulletin.objects.filter(
                    trimester=bulletin.trimester,
                    student__current_class=bulletin.student.current_class
                ).order_by('student_average')
                
                class_highest = 0
                class_lowest = 20
                standard_deviation = 0
                
                if all_class_bulletins.exists():
                    averages = [float(b.student_average) for b in all_class_bulletins]
                    class_highest = max(averages)
                    class_lowest = min(averages)
                    
                    mean = sum(averages) / len(averages)
                    variance = sum((x - mean) ** 2 for x in averages) / len(averages)
                    standard_deviation = variance ** 0.5
                
                bulletin_data = {
                    'bulletin': bulletin,
                    'school_name': school_name,
                    'bulletin_lines_with_grades': bulletin_lines_with_grades,
                    'group1_average': group1_average,
                    'group1_coefficient': group1_coefficient,
                    'group1_points': group1_points,
                    'group2_average': group2_average,
                    'group2_coefficient': group2_coefficient,
                    'group2_points': group2_points,
                    'previous_averages': previous_averages,
                    'class_highest': class_highest,
                    'class_lowest': class_lowest,
                    'standard_deviation': standard_deviation,
                    'conduct': {},
                    'work_appreciation': {},
                    'supervisor_observations': '',
                    'parent_observations': '',
                    'main_teacher_visa': '',
                    'progress_status': 'En cours'
                }
                
                bulletins_data.append(bulletin_data)
            
            # Générer le PDF groupé
            html_string = render_to_string('notes/bulletin_pdf_batch.html', {
                'bulletins_data': bulletins_data,
                'school_name': school_name,
                'school_address': school_address,
                'school_phone': school_phone,
                'generated_at': timezone.now(),
            })
            
            html = HTML(string=html_string)
            pdf = html.write_pdf()
            
            # Nom du fichier
            filename = f"bulletins_lot_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            messages.success(request, f"{len(bulletins_data)} bulletins générés avec succès en PDF.")
            return response
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du PDF groupé: {str(e)}")
            return redirect('notes:bulletin_list')
    
    # Affichage du formulaire de sélection
    context = {
        'trimesters': Trimester.objects.filter(year=year),
        'classes': SchoolClass.objects.filter(year=year),
        'year': year,
    }
    
    return render(request, 'notes/bulletin_pdf_batch_form.html', context)

# ==================== AJAX ENDPOINTS ====================

@login_required
def get_classes_for_trimester(request, trimester_id):
    """Récupérer les classes pour un trimestre"""
    trimester = get_object_or_404(Trimester, pk=trimester_id)
    classes = SchoolClass.objects.filter(year=trimester.year)
    
    data = [{'id': cls.id, 'name': str(cls)} for cls in classes]
    return JsonResponse({'classes': data})

@login_required
def get_subjects_for_class(request, class_id):
    """Récupérer les matières pour une classe"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Récupérer les matières enseignées dans cette classe avec leurs coefficients
    teaching_assignments = TeachingAssignment.objects.filter(
        school_class=school_class,
        year=year
    ).select_related('subject')
    
    data = []
    for assignment in teaching_assignments:
        data.append({
            'id': assignment.subject.id,
            'name': assignment.subject.name,
            'coefficient': assignment.coefficient
        })
    
    return JsonResponse({'subjects': data})

@login_required
def get_students_for_evaluation(request, evaluation_id):
    """Récupérer les étudiants pour une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    students = Student.objects.filter(
        current_class=evaluation.school_class,
        year=evaluation.trimester.year,
        is_active=True
    ).order_by('last_name', 'first_name')
    
    data = [{
        'id': student.id,
        'name': f"{student.last_name.upper()} {student.first_name}",
        'matricule': student.matricule
    } for student in students]
    return JsonResponse({'students': data})

@login_required
@require_http_methods(["POST"])
def save_grade_ajax(request):
    """Sauvegarder une note via AJAX"""
    try:
        data = json.loads(request.body)
        evaluation_id = data.get('evaluation_id')
        student_id = data.get('student_id')
        score = data.get('score')
        remarks = data.get('remarks', '')
        
        evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
        student = get_object_or_404(Student, pk=student_id)
        
        # Vérifier que l'évaluation est ouverte
        if not evaluation.is_open:
            return JsonResponse({'error': 'Cette évaluation est fermée'}, status=400)
        
        # Créer ou mettre à jour la note
        grade, created = StudentGrade.objects.update_or_create(
            student=student,
            evaluation=evaluation,
            defaults={
                'score': score,
                'remarks': remarks,
                'graded_by': request.user
            }
        )
        
        return JsonResponse({
            'success': True,
            'created': created,
            'grade_id': grade.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_evaluation_stats(request, evaluation_id):
    """Récupérer les statistiques d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    grades = StudentGrade.objects.filter(evaluation=evaluation)
    
    if grades.exists():
        stats = {
            'total_students': grades.count(),
            'average_score': round(grades.aggregate(avg=Avg('score'))['avg'], 2),
            'success_rate': round(grades.filter(score__gte=10).count() / grades.count() * 100, 1),
            'highest_score': grades.aggregate(max=models.Max('score'))['score__max'],
            'lowest_score': grades.aggregate(min=models.Min('score'))['score__min'],
        }
    else:
        stats = {
            'total_students': 0,
            'average_score': 0,
            'success_rate': 0,
            'highest_score': 0,
            'lowest_score': 0,
        }
    
    return JsonResponse(stats)

# ==================== RAPPORTS ET STATISTIQUES ====================

@login_required
@user_passes_test(is_admin_or_direction)
def reports_dashboard(request):
    """Dashboard des rapports"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    # Statistiques générales
    total_students = Student.objects.filter(year=year, is_active=True).count()
    total_evaluations = Evaluation.objects.filter(trimester__year=year).count()
    total_grades = StudentGrade.objects.filter(evaluation__trimester__year=year).count()
    
    # Moyenne générale
    avg_score = StudentGrade.objects.filter(
        evaluation__trimester__year=year
    ).aggregate(avg=Avg('score'))['avg'] or 0
    
    context = {
        'total_students': total_students,
        'total_evaluations': total_evaluations,
        'total_grades': total_grades,
        'avg_score': avg_score,
    }
    return render(request, 'notes/reports_dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def class_performance_report(request, class_id):
    """Rapport de performance d'une classe"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    
    context = {
        'school_class': school_class,
    }
    return render(request, 'notes/class_performance_report.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def student_progress_report(request, student_id):
    """Rapport de progression d'un étudiant"""
    student = get_object_or_404(Student, pk=student_id)
    
    context = {
        'student': student,
    }
    return render(request, 'notes/student_progress_report.html', context)

@login_required
@user_passes_test(is_admin_or_direction)
def subject_analysis_report(request, subject_id):
    """Rapport d'analyse d'une matière"""
    subject = get_object_or_404(Subject, pk=subject_id)
    
    context = {
        'subject': subject,
    }
    return render(request, 'notes/subject_analysis_report.html', context)

# ==================== IMPORT/EXPORT ====================

@login_required
@user_passes_test(is_teacher_or_admin)
def import_export_dashboard(request):
    """Dashboard import/export"""
    return render(request, 'notes/import_export_dashboard.html')

@login_required
@user_passes_test(is_teacher_or_admin)
def export_grades(request, evaluation_id):
    """Exporter les notes d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    
    # Logique d'export Excel
    pass

@login_required
@user_passes_test(is_teacher_or_admin)
def import_grades(request, evaluation_id):
    """Importer les notes d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    
    if request.method == 'POST':
        # Logique d'import Excel
        pass
    
    return render(request, 'notes/import_grades.html', {'evaluation': evaluation})

@login_required
@user_passes_test(is_teacher_or_admin)
def class_evaluations_list(request, class_id):
    """Liste des évaluations pour une classe spécifique"""
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    school_class = get_object_or_404(SchoolClass, pk=class_id, year=year)
    
    evaluations = Evaluation.objects.filter(
        school_class=school_class,
        trimester__year=year
    ).select_related('trimester', 'subject').prefetch_related('grades').order_by('-created_at')
    
    # Filtres
    trimester_filter = request.GET.get('trimester')
    subject_filter = request.GET.get('subject')
    status_filter = request.GET.get('status')
    
    if trimester_filter:
        evaluations = evaluations.filter(trimester_id=trimester_filter)
    if subject_filter:
        evaluations = evaluations.filter(subject_id=subject_filter)
    if status_filter == 'open':
        evaluations = evaluations.filter(is_open=True)
    elif status_filter == 'closed':
        evaluations = evaluations.filter(is_open=False)
    
    # Statistiques de la classe
    total_students = school_class.students.count()
    total_evaluations = evaluations.count()
    total_grades = sum(evaluation.grades.count() for evaluation in evaluations)
    completed_evaluations = sum(1 for evaluation in evaluations if evaluation.grades.count() >= total_students)
    
    # Vérifier si on peut générer des bulletins
    can_generate_bulletins = False
    ready_trimester = None
    for trimester in Trimester.objects.filter(year=year):
        trimester_evaluations = evaluations.filter(trimester=trimester)
        if trimester_evaluations.exists():
            trimester_completed = sum(1 for e in trimester_evaluations if e.grades.count() >= total_students)
            if trimester_completed == trimester_evaluations.count():
                can_generate_bulletins = True
                ready_trimester = trimester
                break
    
    # Pagination
    paginator = Paginator(evaluations, 12)  # 12 évaluations par page
    page_number = request.GET.get('page')
    evaluations_page = paginator.get_page(page_number)
    
    context = {
        'school_class': school_class,
        'evaluations': evaluations_page,
        'total_students': total_students,
        'total_evaluations': total_evaluations,
        'total_grades': total_grades,
        'completed_evaluations': completed_evaluations,
        'can_generate_bulletins': can_generate_bulletins,
        'ready_trimester': ready_trimester,
        'trimesters': Trimester.objects.filter(year=year),
        'subjects': Subject.objects.all(),
        'selected_trimester': trimester_filter,
        'selected_subject': subject_filter,
        'status_filter': status_filter,
    }
    return render(request, 'notes/class_evaluations_list.html', context)
