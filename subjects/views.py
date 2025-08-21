import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from .models import Subject, SubjectProgram, LearningUnit, Lesson, LessonProgress
from .forms import SubjectForm, TimetableSlotForm, TimetableBulkForm
from teachers.models import Teacher
from classes.models import SchoolClass, TimetableSlot
from school.models import SchoolYear
from students.models import Student
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.mixins import LoginRequiredMixin

# Liste des matières

def subject_list(request):
    subjects = Subject.objects.all().prefetch_related('teachers')
    teachers = Teacher.objects.all()
    
    # Préparer les enseignants principaux pour chaque matière
    # Format: {subject_id: [teacher1, teacher2, ...]}
    subject_main_teachers = {}
    for subject in subjects:
        main_teachers = Teacher.objects.filter(main_subject=subject)
        subject_main_teachers[subject.id] = list(main_teachers)
    
    # Ajouter les variables pour le sidebar (compatibilité avec le template)
    from students.models import Student
    from classes.models import SchoolClass
    subject_main_teachers['students_count'] = Student.objects.filter(is_active=True).count()
    subject_main_teachers['teachers_count'] = Teacher.objects.filter(is_active=True).count()
    subject_main_teachers['classes_count'] = SchoolClass.objects.filter(is_active=True).count()
    
    return render(request, 'subjects/subject_list.html', {
        'subjects': subjects,
        'teachers': teachers,
        'subject_main_teachers': subject_main_teachers,
        'students_count': subject_main_teachers['students_count'],
        'teachers_count': subject_main_teachers['teachers_count'],
        'classes_count': subject_main_teachers['classes_count'],
    })

# Détail d'une matière

def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    teachers = subject.teachers.all()
    main_teachers = Teacher.objects.filter(main_subject=subject)
    # Ajout des valeurs par défaut si attributs absents
    classes_count = subject.classes.count() if hasattr(subject, 'classes') else 0
    total_students = getattr(subject, 'total_students', 0)
    average_grade = getattr(subject, 'average_grade', "N/A")
    return render(request, 'subjects/subject_detail.html', {
        'subject': subject,
        'teachers': teachers,
        'main_teachers': main_teachers,
        'classes_count': classes_count,
        'total_students': total_students,
        'average_grade': average_grade,
    })

# Création (htmx)
def subject_create_htmx(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            return HttpResponse(status=204)  # htmx: close modal and refresh
    else:
        form = SubjectForm()
    return render(request, 'subjects/partials/subject_form.html', {'form': form, 'subject': None})

# Modification (htmx)
def subject_update_htmx(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204)
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'subjects/partials/subject_form.html', {'form': form, 'subject': subject})

# Suppression (htmx)
def subject_delete_htmx(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return HttpResponse(status=204)
    return render(request, 'subjects/partials/subject_confirm_delete.html', {'subject': subject})

@require_POST
def subject_create_ajax(request):
    form = SubjectForm(request.POST)
    if form.is_valid():
        subject = form.save()
        return JsonResponse({'success': True, 'subject_id': subject.id, 'name': subject.name})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@require_POST
def subject_update_ajax(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST, instance=subject)
    if form.is_valid():
        subject = form.save()
        return JsonResponse({'success': True, 'subject_id': subject.id, 'name': subject.name})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@require_POST
def subject_delete_ajax(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    return JsonResponse({'success': True})

@require_GET
def subject_detail_ajax(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    data = {
        'id': subject.id,
        'name': getattr(subject, 'name', ''),
        'code': getattr(subject, 'code', ''),
        'description': getattr(subject, 'description', ''),
        'teachers': [t.id for t in subject.teachers.all()],
    }
    return JsonResponse({'success': True, 'subject': data})


# ============================================================================
# VUES PÉDAGOGIQUES - Gestion des Programmes et Unités d'Apprentissage
# ============================================================================

@login_required
def pedagogy_dashboard(request):
    """
    Tableau de bord principal de la gestion pédagogique.
    Affiche un aperçu global des programmes, unités et leçons.
    """
    # Récupération des données globales
    total_subjects = Subject.objects.count()
    total_programs = SubjectProgram.objects.count()
    total_units = LearningUnit.objects.count()
    total_lessons = Lesson.objects.count()
    
    # Programmes actifs
    active_programs = SubjectProgram.objects.filter(is_active=True).select_related(
        'subject', 'school_class', 'school_year'
    ).prefetch_related('learning_units')
    
    # Leçons récentes
    recent_lessons = Lesson.objects.select_related(
        'learning_unit__subject_program__subject',
        'teacher'
    ).order_by('-created_at')[:10]
    
    # Statistiques de progression
    programs_completion = []
    for program in active_programs:
        completion = program.get_completion_percentage()
        programs_completion.append({
            'program': program,
            'completion': completion,
            'remaining_hours': program.get_remaining_hours()
        })
    
    context = {
        'total_subjects': total_subjects,
        'total_programs': total_programs,
        'total_units': total_units,
        'total_lessons': total_lessons,
        'active_programs': active_programs,
        'recent_lessons': recent_lessons,
        'programs_completion': programs_completion,
    }
    
    return render(request, 'subjects/pedagogy/dashboard.html', context)


@login_required
def program_list(request):
    """
    Liste de tous les programmes pédagogiques avec filtres et recherche.
    """
    programs = SubjectProgram.objects.select_related(
        'subject', 'school_class', 'school_year', 'created_by'
    ).prefetch_related('learning_units')
    
    # Filtres
    subject_filter = request.GET.get('subject')
    class_filter = request.GET.get('class')
    year_filter = request.GET.get('year')
    status_filter = request.GET.get('status')
    
    if subject_filter:
        programs = programs.filter(subject_id=subject_filter)
    if class_filter:
        programs = programs.filter(school_class_id=class_filter)
    if year_filter:
        programs = programs.filter(school_year_id=year_filter)
    if status_filter:
        if status_filter == 'active':
            programs = programs.filter(is_active=True)
        elif status_filter == 'inactive':
            programs = programs.filter(is_active=False)
        elif status_filter == 'approved':
            programs = programs.filter(is_approved=True)
        elif status_filter == 'pending':
            programs = programs.filter(is_approved=False)
    
    # Options pour les filtres
    subjects = Subject.objects.all()
    classes = SchoolClass.objects.all()
    years = SchoolYear.objects.all()
    
    context = {
        'programs': programs,
        'subjects': subjects,
        'classes': classes,
        'years': years,
        'filters': {
            'subject': subject_filter,
            'class': class_filter,
            'year': year_filter,
            'status': status_filter,
        }
    }
    
    return render(request, 'subjects/pedagogy/program_list.html', context)


@login_required
def program_detail(request, pk):
    """
    Détail d'un programme pédagogique avec ses unités et statistiques.
    """
    program = get_object_or_404(SubjectProgram.objects.select_related(
        'subject', 'school_class', 'school_year', 'created_by'
    ).prefetch_related('learning_units__lessons'), pk=pk)
    
    # Statistiques du programme
    total_units = program.learning_units.count()
    total_lessons = sum(unit.lessons.count() for unit in program.learning_units.all())
    completed_lessons = sum(
        unit.lessons.filter(status='COMPLETED').count() 
        for unit in program.learning_units.all()
    )
    
    # Progression par unité
    units_progress = []
    for unit in program.learning_units.all():
        progress = {
            'unit': unit,
            'completion': unit.get_completion_percentage(),
            'lessons_count': unit.lessons.count(),
            'completed_lessons': unit.lessons.filter(status='COMPLETED').count(),
            'can_start': unit.can_be_started(),
        }
        units_progress.append(progress)
    
    # Leçons récentes
    recent_lessons = Lesson.objects.filter(
        learning_unit__subject_program=program
    ).select_related('learning_unit', 'teacher').order_by('-created_at')[:5]
    
    context = {
        'program': program,
        'total_units': total_units,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'units_progress': units_progress,
        'recent_lessons': recent_lessons,
    }
    
    return render(request, 'subjects/pedagogy/program_detail.html', context)


@login_required
def unit_detail(request, pk):
    """
    Détail d'une unité d'apprentissage avec ses leçons et progression.
    """
    unit = get_object_or_404(LearningUnit.objects.select_related(
        'subject_program__subject', 'subject_program__school_class'
    ).prefetch_related('lessons__student_progress', 'prerequisites'), pk=pk)
    
    # Leçons de l'unité
    lessons = unit.lessons.select_related('teacher', 'timetable_slot').order_by('order', 'planned_date')
    
    # Statistiques de l'unité
    total_lessons = lessons.count()
    completed_lessons = lessons.filter(status='COMPLETED').count()
    in_progress_lessons = lessons.filter(status='IN_PROGRESS').count()
    planned_lessons = lessons.filter(status='PLANNED').count()
    
    # Progression des élèves (si des leçons ont été terminées)
    student_progress = {}
    if completed_lessons > 0:
        for lesson in lessons.filter(status='COMPLETED'):
            for progress in lesson.student_progress.all():
                student_id = progress.student.id
                if student_id not in student_progress:
                    student_progress[student_id] = {
                        'student': progress.student,
                        'total_lessons': 0,
                        'completed_lessons': 0,
                        'avg_understanding': 0,
                        'avg_participation': 0,
                    }
                
                student_progress[student_id]['total_lessons'] += 1
                student_progress[student_id]['completed_lessons'] += 1
                student_progress[student_id]['avg_understanding'] += progress.understanding_level
                student_progress[student_id]['avg_participation'] += progress.participation
        
        # Calcul des moyennes
        for student_data in student_progress.values():
            if student_data['completed_lessons'] > 0:
                student_data['avg_understanding'] = round(
                    student_data['avg_understanding'] / student_data['completed_lessons'], 1
                )
                student_data['avg_participation'] = round(
                    student_data['avg_participation'] / student_data['completed_lessons'], 1
                )
    
    context = {
        'unit': unit,
        'lessons': lessons,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'in_progress_lessons': in_progress_lessons,
        'planned_lessons': planned_lessons,
        'student_progress': list(student_progress.values()),
    }
    
    return render(request, 'subjects/pedagogy/unit_detail.html', context)


@login_required
def lesson_detail(request, pk):
    """Vue détaillée d'une leçon"""
    lesson = get_object_or_404(Lesson, pk=pk)
    
    # Récupérer les informations de progression
    unit_progress = lesson.learning_unit.get_completion_percentage()
    program_progress = lesson.learning_unit.subject_program.get_completion_percentage()
    
    context = {
        'lesson': lesson,
        'unit_progress': unit_progress,
        'program_progress': program_progress,
    }
    
    return render(request, 'subjects/pedagogy/lesson_detail.html', context)

@login_required
def lesson_change_status(request, pk):
    """Vue pour changer le statut d'une leçon"""
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Lesson.STATUS_CHOICES):
            old_status = lesson.status
            lesson.status = new_status
            
            # Mettre à jour la date effective si la leçon est terminée
            if new_status == 'COMPLETED':
                lesson.actual_date = timezone.now().date()
                lesson.completion_percentage = 100
            elif new_status == 'IN_PROGRESS':
                lesson.actual_date = timezone.now().date()
                lesson.completion_percentage = 50
            
            lesson.save()
            
            messages.success(request, f"Statut de la leçon '{lesson.title}' changé de {dict(Lesson.STATUS_CHOICES)[old_status]} à {dict(Lesson.STATUS_CHOICES)[new_status]}")
            
            # Rediriger vers la page de détail de la leçon
            return redirect('subjects:lesson_detail', pk=pk)
        else:
            messages.error(request, "Statut invalide")
    
    return redirect('subjects:lesson_detail', pk=pk)

@login_required
def generate_timetable_from_programs(request, class_id):
    """Génère automatiquement l'emploi du temps à partir des programmes pédagogiques"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    
    if request.method == 'POST':
        try:
            # Récupérer tous les programmes pédagogiques actifs de la classe
            programs = SubjectProgram.objects.filter(
                school_class=school_class,
                is_active=True
            ).select_related('subject')
            
            if not programs.exists():
                messages.warning(request, "Aucun programme pédagogique actif trouvé pour cette classe.")
                return redirect('classes:schoolclass_detail', pk=class_id)
            
            # Supprimer l'ancien emploi du temps
            from classes.models import TimetableSlot
            old_slots_count = TimetableSlot.objects.filter(class_obj=school_class).count()
            TimetableSlot.objects.filter(class_obj=school_class).delete()
            
            # Récupérer tous les enseignants actifs de l'école
            from teachers.models import Teacher
            available_teachers = Teacher.objects.filter(
                is_active=True,
                school=school_class.school,
                year=school_class.year
            )
            
            if not available_teachers.exists():
                messages.error(request, "Aucun enseignant disponible pour cette école et année.")
                return redirect('classes:schoolclass_detail', pk=class_id)
            
            # Créer un mapping matière -> enseignant
            subject_teacher_mapping = {}
            for teacher in available_teachers:
                if teacher.main_subject:
                    subject_teacher_mapping[teacher.main_subject.id] = teacher
            
            # Limite réaliste : 36h de cours par semaine maximum
            MAX_HOURS_PER_WEEK = 36
            days_per_week = 5
            periods_per_day = 8
            
            # Calculer le total des heures demandées
            total_hours_requested = sum(program.total_hours for program in programs)
            
            if total_hours_requested > MAX_HOURS_PER_WEEK:
                messages.warning(request, 
                    f"Total demandé: {total_hours_requested}h/semaine. "
                    f"Limite fixée à {MAX_HOURS_PER_WEEK}h/semaine pour respecter la réalité scolaire.")
            
            # Répartir proportionnellement les heures si on dépasse la limite
            if total_hours_requested > MAX_HOURS_PER_WEEK:
                reduction_factor = MAX_HOURS_PER_WEEK / total_hours_requested
                for program in programs:
                    program.adjusted_hours = max(1, int(program.total_hours * reduction_factor))
            else:
                for program in programs:
                    program.adjusted_hours = program.total_hours
            
            # Générer le nouvel emploi du temps
            slots_created = 0
            current_year = school_class.year
            
            # Créer une grille pour éviter les conflits
            timetable_grid = {}
            for day in range(1, days_per_week + 1):
                timetable_grid[day] = set()
            
            # Détails de la répartition pour le message
            subject_details = []
            
            for program in programs:
                subject = program.subject
                hours_per_week = program.adjusted_hours
                
                # Trouver un enseignant pour cette matière
                teacher = None
                if subject.id in subject_teacher_mapping:
                    teacher = subject_teacher_mapping[subject.id]
                else:
                    # Si aucun enseignant principal, prendre le premier disponible
                    teacher = available_teachers.first()
                
                if not teacher:
                    messages.warning(request, f"Aucun enseignant disponible pour la matière {subject.name}")
                    continue
                
                # Répartir les heures sur la semaine de manière équilibrée
                slots_needed = max(1, hours_per_week)
                
                # Calculer la répartition optimale
                slots_per_day = slots_needed // days_per_week
                remaining_slots = slots_needed % days_per_week
                
                subject_slots_created = 0
                
                for day in range(1, days_per_week + 1):
                    day_slots = slots_per_day
                    if remaining_slots > 0:
                        day_slots += 1
                        remaining_slots -= 1
                    
                    if day_slots == 0:
                        continue
                    
                    # Trouver des créneaux disponibles pour ce jour
                    available_periods = []
                    for period in range(1, periods_per_day + 1):
                        if period not in timetable_grid[day]:
                            available_periods.append(period)
                    
                    # Créer les créneaux pour ce jour
                    for i in range(min(day_slots, len(available_periods))):
                        period = available_periods[i]
                        
                        # Créer le créneau
                        slot = TimetableSlot.objects.create(
                            class_obj=school_class,
                            subject=subject,
                            teacher=teacher,
                            day=day,
                            period=period,
                            duration=1,  # 1 heure par défaut
                            year=current_year
                        )
                        
                        # Marquer le créneau comme occupé
                        timetable_grid[day].add(period)
                        slots_created += 1
                        subject_slots_created += 1
                
                # Ajouter les détails pour cette matière
                subject_details.append({
                    'name': subject.name,
                    'requested': program.total_hours,
                    'adjusted': program.adjusted_hours,
                    'created': subject_slots_created,
                    'teacher': teacher.get_full_name()
                })
            
            if slots_created > 0:
                total_hours_created = slots_created
                
                # Message de succès détaillé
                success_msg = f"Emploi du temps généré avec succès ! {slots_created} créneaux créés ({total_hours_created}h/semaine)"
                if old_slots_count > 0:
                    success_msg += f" (remplace {old_slots_count} anciens créneaux)"
                
                messages.success(request, success_msg)
                
                # Message détaillé de la répartition
                details_msg = "Répartition par matière: "
                for detail in subject_details:
                    if detail['requested'] != detail['adjusted']:
                        details_msg += f"{detail['name']}: {detail['requested']}h→{detail['adjusted']}h, "
                    else:
                        details_msg += f"{detail['name']}: {detail['adjusted']}h, "
                
                details_msg = details_msg.rstrip(", ")
                messages.info(request, details_msg)
                
                # Afficher un résumé de la répartition
                if total_hours_requested > MAX_HOURS_PER_WEEK:
                    messages.info(request, 
                        f"Note: Les heures ont été ajustées de {total_hours_requested}h "
                        f"à {total_hours_created}h pour respecter la limite de {MAX_HOURS_PER_WEEK}h/semaine")
                
                # Rediriger avec un paramètre pour forcer le rafraîchissement
                return redirect(f'classes:schoolclass_detail?refresh=1&pk={class_id}')
            else:
                messages.warning(request, "Aucun créneau n'a pu être créé. Vérifiez que des enseignants sont disponibles.")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération de l'emploi du temps : {str(e)}")
            import traceback
            traceback.print_exc()
    
    return redirect('classes:schoolclass_detail', pk=class_id)


@login_required
def class_pedagogy_overview(request, class_id):
    """
    Vue d'ensemble pédagogique pour une classe spécifique.
    Intégrée dans l'interface de détail de classe.
    """
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    
    # Programmes pédagogiques de la classe
    programs = SubjectProgram.objects.filter(
        school_class=school_class,
        is_active=True
    ).select_related('subject', 'school_year').prefetch_related('learning_units')
    
    # Statistiques globales de la classe
    total_subjects = programs.count()
    total_units = sum(program.learning_units.count() for program in programs)
    total_lessons = sum(
        sum(unit.lessons.count() for unit in program.learning_units.all())
        for program in programs
    )
    
    # Progression par matière
    subjects_progress = []
    for program in programs:
        completion = program.get_completion_percentage()
        subjects_progress.append({
            'subject': program.subject,
            'completion': completion,
            'units_count': program.learning_units.count(),
            'lessons_count': sum(unit.lessons.count() for unit in program.learning_units.all()),
        })
    
    # Leçons récentes de la classe
    recent_lessons = Lesson.objects.filter(
        learning_unit__subject_program__school_class=school_class
    ).select_related(
        'learning_unit__subject_program__subject',
        'teacher'
    ).order_by('-created_at')[:10]
    
    context = {
        'school_class': school_class,
        'programs': programs,
        'total_subjects': total_subjects,
        'total_units': total_units,
        'total_lessons': total_lessons,
        'subjects_progress': subjects_progress,
        'recent_lessons': recent_lessons,
    }
    
    return render(request, 'subjects/pedagogy/class_overview.html', context)


@login_required
def student_pedagogy_progress(request, student_id):
    """
    Vue de la progression pédagogique d'un élève spécifique.
    """
    student = get_object_or_404(Student, pk=student_id)
    
    # Progression de l'élève par leçon
    lesson_progress = LessonProgress.objects.filter(
        student=student
    ).select_related(
        'lesson__learning_unit__subject_program__subject',
        'lesson__teacher'
    ).order_by('-created_at')
    
    # Statistiques de l'élève
    total_lessons = lesson_progress.count()
    completed_homework = lesson_progress.filter(homework_completed=True).count()
    avg_understanding = lesson_progress.aggregate(avg=Avg('understanding_level'))['avg'] or 0
    avg_participation = lesson_progress.aggregate(avg=Avg('participation'))['avg'] or 0
    
    # Progression par matière
    subjects_progress = {}
    for progress in lesson_progress:
        subject = progress.lesson.learning_unit.subject_program.subject
        if subject.id not in subjects_progress:
            subjects_progress[subject.id] = {
                'subject': subject,
                'lessons_count': 0,
                'avg_understanding': 0,
                'avg_participation': 0,
                'homework_completed': 0,
            }
        
        subjects_progress[subject.id]['lessons_count'] += 1
        subjects_progress[subject.id]['avg_understanding'] += progress.understanding_level
        subjects_progress[subject.id]['avg_participation'] += progress.participation
        if progress.homework_completed:
            subjects_progress[subject.id]['homework_completed'] += 1
    
    # Calcul des moyennes
    for subject_data in subjects_progress.values():
        if subject_data['lessons_count'] > 0:
            subject_data['avg_understanding'] = round(
                subject_data['avg_understanding'] / subject_data['lessons_count'], 1
            )
            subject_data['avg_participation'] = round(
                subject_data['avg_participation'] / subject_data['lessons_count'], 1
            )
    
    context = {
        'student': student,
        'lesson_progress': lesson_progress,
        'total_lessons': total_lessons,
        'completed_homework': completed_homework,
        'avg_understanding': round(avg_understanding, 1),
        'avg_participation': round(avg_participation, 1),
        'subjects_progress': list(subjects_progress.values()),
    }
    
    return render(request, 'subjects/pedagogy/student_progress.html', context)

@login_required
def program_create(request):
    """
    Vue pour créer un nouveau programme pédagogique.
    """
    from .forms import SubjectProgramForm
    
    if request.method == 'POST':
        form = SubjectProgramForm(request.POST)
        if form.is_valid():
            program = form.save(commit=False)
            program.created_by = request.user
            program.save()
            messages.success(request, f'Programme "{program.title}" créé avec succès !')
            return redirect('subjects:pedagogy_dashboard')
    else:
        form = SubjectProgramForm()
    
    context = {
        'form': form,
        'title': 'Nouveau Programme Pédagogique',
    }
    
    return render(request, 'subjects/pedagogy/program_form.html', context)

@login_required
def timetable_management(request, class_id):
    """Vue pour gérer manuellement l'emploi du temps d'une classe"""
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    
    # Récupérer les créneaux existants
    timetable_slots = TimetableSlot.objects.filter(
        class_obj=school_class,
        year=school_class.year
    ).select_related('subject', 'teacher').order_by('day', 'period')
    
    # Récupérer les programmes pédagogiques pour cette classe
    programs = SubjectProgram.objects.filter(
        school_class=school_class,
        is_active=True
    ).select_related('subject')
    
    # Formulaire pour créer un nouveau créneau
    if request.method == 'POST':
        if 'create_slot' in request.POST:
            form = TimetableSlotForm(request.POST, school_class=school_class)
            if form.is_valid():
                slot = form.save(commit=False)
                slot.class_obj = school_class
                slot.year = school_class.year
                slot.save()
                messages.success(request, f"Créneau créé : {slot.subject.name} le {slot.get_day_display()}")
                return redirect('subjects:timetable_management', class_id=class_id)
        elif 'bulk_assign' in request.POST:
            bulk_form = TimetableBulkForm(request.POST, school_class=school_class)
            if bulk_form.is_valid():
                # Traiter l'affectation en masse
                slots_created = process_bulk_assignment(bulk_form, school_class)
                messages.success(request, f"{slots_created} créneaux créés pour {bulk_form.cleaned_data['subject'].name}")
                return redirect('subjects:timetable_management', class_id=class_id)
    else:
        form = TimetableSlotForm(school_class=school_class)
        bulk_form = TimetableBulkForm(school_class=school_class)
    
    # Organiser les créneaux par jour
    timetable_by_day = {}
    for day in range(1, 6):
        timetable_by_day[day] = timetable_slots.filter(day=day).order_by('period')
    
    context = {
        'school_class': school_class,
        'timetable_slots': timetable_slots,
        'timetable_by_day': timetable_by_day,
        'programs': programs,
        'form': form,
        'bulk_form': bulk_form,
        'total_hours': sum(program.total_hours for program in programs),
        'max_hours_per_week': 36,
    }
    
    return render(request, 'subjects/pedagogy/timetable_management.html', context)

def process_bulk_assignment(form, school_class):
    """Traite l'affectation en masse des matières aux créneaux"""
    subject = form.cleaned_data['subject']
    teacher = form.cleaned_data['teacher']
    hours_per_week = form.cleaned_data['hours_per_week']
    repartition_type = form.cleaned_data['repartition_type']
    
    # Supprimer les anciens créneaux pour cette matière et cette classe
    TimetableSlot.objects.filter(
        class_obj=school_class,
        subject=subject
    ).delete()
    
    slots_created = 0
    
    if repartition_type == 'balanced':
        # Répartition équilibrée : 1h par jour
        hours_per_day = hours_per_week // 5
        remaining_hours = hours_per_week % 5
        
        for day in range(1, 6):
            day_hours = hours_per_day
            if remaining_hours > 0:
                day_hours += 1
                remaining_hours -= 1
            
            if day_hours > 0:
                # Trouver des créneaux disponibles
                available_periods = find_available_periods(school_class, day, day_hours)
                for period in available_periods:
                    TimetableSlot.objects.create(
                        class_obj=school_class,
                        subject=subject,
                        teacher=teacher,
                        day=day,
                        period=period,
                        duration=1,
                        year=school_class.year
                    )
                    slots_created += 1
    
    elif repartition_type == 'concentrated':
        # Répartition concentrée : 2h par jour
        days_needed = (hours_per_week + 1) // 2  # Arrondir vers le haut
        
        for day in range(1, min(days_needed + 1, 6)):
            day_hours = min(2, hours_per_week - (day - 1) * 2)
            if day_hours > 0:
                available_periods = find_available_periods(school_class, day, day_hours)
                for period in available_periods:
                    TimetableSlot.objects.create(
                        class_obj=school_class,
                        subject=subject,
                        teacher=teacher,
                        day=day,
                        period=period,
                        duration=1,
                        year=school_class.year
                    )
                    slots_created += 1
    
    elif repartition_type == 'custom':
        # Répartition personnalisée
        days_hours = {
            1: form.cleaned_data['monday_hours'],
            2: form.cleaned_data['tuesday_hours'],
            3: form.cleaned_data['wednesday_hours'],
            4: form.cleaned_data['thursday_hours'],
            5: form.cleaned_data['friday_hours'],
        }
        
        for day, hours in days_hours.items():
            if hours > 0:
                available_periods = find_available_periods(school_class, day, hours)
                for period in available_periods:
                    TimetableSlot.objects.create(
                        class_obj=school_class,
                        subject=subject,
                        teacher=teacher,
                        day=day,
                        period=period,
                        duration=1,
                        year=school_class.year
                    )
                    slots_created += 1
    
    return slots_created

def find_available_periods(school_class, day, hours_needed):
    """Trouve des périodes disponibles pour un jour donné"""
    occupied_periods = set(
        TimetableSlot.objects.filter(
            class_obj=school_class,
            day=day
        ).values_list('period', flat=True)
    )
    
    available_periods = []
    for period in range(1, 9):  # 8 périodes par jour
        if period not in occupied_periods:
            available_periods.append(period)
            if len(available_periods) >= hours_needed:
                break
    
    return available_periods

@login_required
def timetable_slot_edit(request, slot_id):
    """Vue pour modifier un créneau horaire"""
    slot = get_object_or_404(TimetableSlot, pk=slot_id)
    
    if request.method == 'POST':
        form = TimetableSlotForm(request.POST, instance=slot, school_class=slot.class_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Créneau modifié avec succès")
            return redirect('subjects:timetable_management', class_id=slot.class_obj.id)
    else:
        form = TimetableSlotForm(instance=slot, school_class=slot.class_obj)
    
    context = {
        'form': form,
        'slot': slot,
        'school_class': slot.class_obj,
    }
    
    return render(request, 'subjects/pedagogy/timetable_slot_edit.html', context)

@login_required
def timetable_slot_delete(request, slot_id):
    """Vue pour supprimer un créneau horaire"""
    slot = get_object_or_404(TimetableSlot, pk=slot_id)
    class_id = slot.class_obj.id
    
    if request.method == 'POST':
        subject_name = slot.subject.name
        slot.delete()
        messages.success(request, f"C Créneau {subject_name} supprimé")
        return redirect('subjects:timetable_management', class_id=class_id)
    
    context = {
        'slot': slot,
        'school_class': slot.class_obj,
    }
    return render(request, 'subjects/pedagogy/timetable_slot_confirm_delete.html', context)


@login_required
def create_timetable_slots(request, class_id):
    """Vue AJAX pour créer des créneaux d'emploi du temps depuis la modale"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        school_class = get_object_or_404(SchoolClass, pk=class_id)
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher')
        hours = request.POST.get('hours', 0)
        slots_json = request.POST.get('slots')
        
        if not all([subject_id, teacher_id, hours, slots_json]):
            return JsonResponse({'success': False, 'error': 'Tous les champs sont obligatoires'})
        
        # Valider que les heures sont un nombre valide
        try:
            hours = float(hours)
            if hours <= 0:
                return JsonResponse({'success': False, 'error': 'Le nombre d\'heures doit être supérieur à 0'})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Le nombre d\'heures doit être un nombre valide'})
        
        # Récupérer les objets
        subject = get_object_or_404(Subject, pk=subject_id)
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        slots = json.loads(slots_json)
        
        if not slots:
            return JsonResponse({'success': False, 'error': 'Au moins un créneau doit être sélectionné'})
        
        # Convertir les heures en entier pour la validation
        hours_int = int(hours)
        if len(slots) != hours_int:
            return JsonResponse({'success': False, 'error': f'Le nombre de créneaux sélectionnés ({len(slots)}) doit correspondre au nombre d\'heures ({hours_int})'})
        
        # Supprimer les anciens créneaux pour cette matière et cette classe
        TimetableSlot.objects.filter(
            class_obj=school_class,
            subject=subject
        ).delete()
        
        slots_created = 0
        
        # Créer les créneaux pour chaque créneau sélectionné
        for slot_info in slots:
            # Format attendu: "jour-période" (ex: "1-2" pour lundi, 2ème période)
            day, period = slot_info.split('-')
            day = int(day)
            period = int(period)
            
            # Vérifier que le créneau n'est pas déjà occupé
            existing_slot = TimetableSlot.objects.filter(
                class_obj=school_class,
                day=day,
                period=period,
                year=school_class.year
            ).first()
            
            if existing_slot:
                return JsonResponse({
                    'success': False, 
                    'error': f'Le créneau {existing_slot.get_day_display()} {existing_slot.get_period_display()} est déjà occupé par {existing_slot.subject.name}'
                })
            
            # Créer le créneau
            TimetableSlot.objects.create(
                class_obj=school_class,
                subject=subject,
                teacher=teacher,
                day=day,
                period=period,
                duration=1,
                year=school_class.year
            )
            slots_created += 1
        
        if slots_created > 0:
            return JsonResponse({
                'success': True, 
                'message': f'{slots_created} créneaux créés pour {subject.name}',
                'slots_created': slots_created
            })
        else:
            return JsonResponse({'success': False, 'error': 'Aucun créneau n\'a pu être créé'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erreur: {str(e)}'})
