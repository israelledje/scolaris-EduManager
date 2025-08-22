import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from .models import SchoolClass, Timetable, TimetableSlot
from .forms import SchoolClassForm, TimetableForm, TimetableSlotForm
from django.contrib.auth.decorators import login_required
import openpyxl
from openpyxl.utils import get_column_letter
from django.template.loader import render_to_string
from django.conf import settings
import tempfile
from django.templatetags.static import static
from io import BytesIO
from teachers.models import TeachingAssignment, Teacher
from subjects.models import Subject
from school.models import SchoolYear, EducationSystem, SchoolLevel
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
import re

# Configuration du logger
logger = logging.getLogger(__name__)

# ---------------------- SchoolClass CRUD HTMX ----------------------

def schoolclass_create_htmx(request):
    if request.method == 'POST':
        form = SchoolClassForm(request.POST)
        if form.is_valid():
            schoolclass = form.save()
            request.session['class_success'] = "Classe créée avec succès !"
            response = HttpResponse()
            response['HX-Redirect'] = reverse('classes:schoolclass_list')
            return response
        else:
            return render(request, 'classes/schoolclass_form.html', {'form': form})
    else:
        form = SchoolClassForm()
        return render(request, 'classes/schoolclass_form.html', {'form': form})

def schoolclass_update_htmx(request, pk):
    schoolclass = get_object_or_404(SchoolClass, pk=pk)
    if request.method == 'POST':
        form = SchoolClassForm(request.POST, instance=schoolclass)
        if form.is_valid():
            schoolclass = form.save()
            request.session['class_success'] = "Classe modifiée avec succès !"
            response = HttpResponse()
            response['HX-Redirect'] = reverse('classes:schoolclass_list')
            return response
        else:
            return render(request, 'classes/schoolclass_form.html', {'form': form, 'schoolclass': schoolclass})
    else:
        form = SchoolClassForm(instance=schoolclass)
        return render(request, 'classes/schoolclass_form.html', {'form': form, 'schoolclass': schoolclass})

def schoolclass_delete_htmx(request, pk):
    schoolclass = get_object_or_404(SchoolClass, pk=pk)
    if request.method == 'POST':
        schoolclass.delete()
        return HttpResponse('')  # htmx peut retirer la ligne côté client
    return render(request, 'classes/schoolclass_confirm_delete.html', {'schoolclass': schoolclass})

# ---------------------- Timetable CRUD HTMX ----------------------

def timetable_create_htmx(request):
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            timetable = form.save()
            return render(request, 'classes/partials/timetable_row.html', {'timetable': timetable, 'created': True})
        else:
            return render(request, 'classes/partials/timetable_form.html', {'form': form})
    else:
        form = TimetableForm()
        return render(request, 'classes/partials/timetable_form.html', {'form': form})

def timetable_update_htmx(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    if request.method == 'POST':
        form = TimetableForm(request.POST, instance=timetable)
        if form.is_valid():
            timetable = form.save()
            return render(request, 'classes/partials/timetable_row.html', {'timetable': timetable, 'updated': True})
        else:
            return render(request, 'classes/partials/timetable_form.html', {'form': form, 'timetable': timetable})
    else:
        form = TimetableForm(instance=timetable)
        return render(request, 'classes/partials/timetable_form.html', {'form': form, 'timetable': timetable})

def timetable_delete_htmx(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    if request.method == 'POST':
        timetable.delete()
        return HttpResponse('')
    return render(request, 'classes/partials/timetable_confirm_delete.html', {'timetable': timetable})

@login_required
def timetable_list(request):
    timetables = Timetable.objects.select_related('school_class', 'year', 'school').order_by('school_class__name')
    return render(request, 'classes/timetable_list.html', {
        'timetables': timetables,
    })

@login_required
def timetable_list_classes(request):
    """
    Affiche la liste des classes pour sélectionner laquelle consulter l'emploi du temps.
    """
    classes = SchoolClass.objects.filter(is_active=True).select_related('level', 'year', 'school', 'main_teacher').order_by('name')
    return render(request, 'classes/timetable_list_classes.html', {
        'classes': classes,
    })

@login_required
def schoolclass_list(request):
    # Vérifier les permissions du professeur
    if request.user.role == 'PROFESSEUR':
        from authentication.permissions import TeacherPermissionManager, require_teacher_assignment
        require_teacher_assignment(request.user)
        permission_manager = TeacherPermissionManager(request.user)
        
        # Récupérer seulement les classes accessibles
        accessible_class_ids = permission_manager.get_accessible_classes()
        if not accessible_class_ids:
            assignment_info = permission_manager.get_assignment_info()
            if not assignment_info['has_assignments']:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied(
                    "Vous n'avez pas encore été assigné à des classes. "
                    "Contactez l'administration pour obtenir vos assignations."
                )
        
        all_classes = SchoolClass.objects.filter(id__in=accessible_class_ids).select_related('level', 'year', 'school', 'main_teacher').prefetch_related('students').order_by('name')
    else:
        # Pour les non-professeurs, afficher toutes les classes
        all_classes = SchoolClass.objects.select_related('level', 'year', 'school', 'main_teacher').prefetch_related('students').order_by('name')
    
    # Statistiques sur les classes accessibles
    total_classes = all_classes.count()
    active_classes = all_classes.filter(is_active=True).count()
    total_students = sum(c.student_count for c in all_classes)
    average_capacity = int(sum(c.capacity for c in all_classes) / total_classes) if total_classes else 0
    
    # Recherche simple
    search = request.GET.get('search', '').strip()
    classes = all_classes
    if search:
        classes = classes.filter(name__icontains=search)
    
    systems = EducationSystem.objects.all()
    class_success = request.session.pop('class_success', None)
    subjects = Subject.objects.all().order_by('name')
    schoolyears = SchoolYear.objects.all().order_by('-annee')
    
    context = {
        'classes': classes,
        'total_classes': total_classes,
        'active_classes': active_classes,
        'total_students': total_students,
        'average_capacity': average_capacity,
        'search': search,
        'systems': systems,
        'class_success': class_success,
        'subjects': subjects,
        'schoolyears': schoolyears,
    }
    
    # Ajouter des informations d'assignation pour les professeurs
    if request.user.role == 'PROFESSEUR':
        context['assignment_info'] = permission_manager.get_assignment_info()
        context['is_teacher_view'] = True
    
    return render(request, 'classes/schoolclass_list.html', context)

@login_required
def schoolclass_detail(request, pk):
    schoolclass = get_object_or_404(SchoolClass, pk=pk)
    students = schoolclass.students.all()
    free_places = schoolclass.capacity - students.count()

    # Récupérer la liste des IDs de matières enseignées
    subject_ids = schoolclass.subject_teached or []
    subjects = list(Subject.objects.filter(id__in=subject_ids).order_by('name'))

    # Récupérer toutes les affectations matière-enseignant pour cette classe et cette année
    teaching_assignments = TeachingAssignment.objects.filter(
        school_class=schoolclass,
        year=schoolclass.year
    ).select_related('teacher', 'subject')

    # Pour chaque matière, construire la liste des enseignants principaux et secondaires
    subject_teachers = {}
    for subject in subjects:
        # Enseignants principaux (main_subject)
        main_teachers = list(Teacher.objects.filter(main_subject=subject, is_active=True))
        # Enseignants affectés via TeachingAssignment
        assigned_teachers = list(
            ta.teacher for ta in teaching_assignments if ta.subject_id == subject.id and ta.teacher is not None
        )
        # Éviter les doublons (un enseignant peut être principal ET affecté)
        assigned_teachers = [t for t in assigned_teachers if t not in main_teachers]
        subject_teachers[subject.id] = {
            'main': main_teachers,
            'assigned': assigned_teachers,
        }

    # Titulaire de la classe (enseignant principal de la classe, pas d'une matière)
    titulaire = schoolclass.main_teacher

    # Récupérer tous les enseignants actifs de la même école et année pour le formulaire de professeur titulaire
    teachers = Teacher.objects.filter(
        is_active=True, 
        school=schoolclass.school, 
        year=schoolclass.year
    ).order_by('last_name', 'first_name')

    # Récupérer les données d'emploi du temps
    from .models import TimetableSlot
    timetable_slots = TimetableSlot.objects.filter(
        class_obj=schoolclass, 
        year=schoolclass.year
    ).select_related('subject', 'teacher').order_by('day', 'period')

    # Construire la grille d'emploi du temps
    timetable_grid = {}
    for day_num, day_name in TimetableSlot.DAY_CHOICES:
        timetable_grid[day_num] = {
            'name': day_name,
            'periods': {}
        }
        for period in range(1, 9):  # 8 créneaux par jour
            # Chercher le créneau correspondant
            slot = None
            for s in timetable_slots:
                if s.day == day_num and s.period == period:
                    slot = s
                    break
            timetable_grid[day_num]['periods'][period] = slot

    # Calculer le total des heures par semaine
    total_hours = sum(ta.hours_per_week or 0 for ta in teaching_assignments)

    # Récupérer les données pédagogiques pour l'onglet pédagogique
    from subjects.models import SubjectProgram, LearningUnit, Lesson
    
    # Programmes pédagogiques de la classe
    programs = SubjectProgram.objects.filter(
        school_class=schoolclass,
        is_active=True
    ).select_related('subject', 'school_year').prefetch_related('learning_units')
    
    # Matières réellement affectées à la classe (pour la modale emploi du temps)
    assigned_subjects = []
    for assignment in teaching_assignments:
        if assignment.subject and assignment.hours_per_week:
            assigned_subjects.append({
                'subject': assignment.subject,
                'hours_per_week': assignment.hours_per_week,
                'teacher': assignment.teacher
            })
    
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
    
    # Calculer la progression moyenne
    avg_completion = 0
    if subjects_progress:
        avg_completion = sum(subject['completion'] for subject in subjects_progress) / len(subjects_progress)
    
    # Leçons récentes de la classe
    recent_lessons = Lesson.objects.filter(
        learning_unit__subject_program__school_class=schoolclass
    ).select_related(
        'learning_unit__subject_program__subject',
        'teacher'
    ).order_by('-created_at')[:10]

    return render(request, 'classes/schoolclass_detail.html', {
        'schoolclass': schoolclass,
        'students': students,
        'free_places': free_places,
        'subjects': subjects,  # liste d'objets Subject
        'subject_teachers': subject_teachers,  # dict {subject_id: {'main': [...], 'assigned': [...]}}
        'teaching_assignments': teaching_assignments,
        'titulaire': titulaire,
        'teachers': teachers,  # Liste des enseignants disponibles pour le professeur titulaire
        'timetable_grid': timetable_grid,  # Grille d'emploi du temps
        'timetable_slots': timetable_slots,  # Créneaux d'emploi du temps
        'total_hours': total_hours,  # Total des heures par semaine
        
        # Données pédagogiques pour l'onglet pédagogique
        'programs': programs,
        'assigned_subjects': assigned_subjects,  # Matières affectées pour l'emploi du temps
        'total_subjects': total_subjects,
        'total_units': total_units,
        'total_lessons': total_lessons,
        'subjects_progress': subjects_progress,
        'recent_lessons': recent_lessons,
        'avg_completion': round(avg_completion, 1),
    })

def export_students_excel(request, class_id):
    schoolclass = SchoolClass.objects.get(id=class_id)
    students = schoolclass.students.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Élèves {schoolclass.name}"

    # En-têtes
    headers = [
        "Nom", "Prénom", "Matricule", "Sexe", "Statut", "Date de naissance"
    ]
    ws.append(headers)

    # Lignes élèves
    for student in students:
        ws.append([
            student.last_name,
            student.first_name,
            student.matricule,
            student.get_gender_display(),
            "Actif" if student.is_active else "Inactif",
            student.birth_date.strftime('%d/%m/%Y') if hasattr(student, 'birth_date') and student.birth_date else ""
        ])

    # Largeur auto
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[column].width = max_length + 2

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=eleves_{schoolclass.name}.xlsx'
    wb.save(response)
    return response

def schoolclass_print_pdf(request, class_id):
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        return HttpResponse("WeasyPrint n'est pas installé.", status=500)

    schoolclass = SchoolClass.objects.get(id=class_id)
    students = schoolclass.students.all()
    teachers = getattr(schoolclass, 'teachers', None)
    assigned_teachers = getattr(schoolclass, 'assigned_teachers', None)
    subjects = getattr(schoolclass, 'subjects', None)
    # Ajoute d'autres données utiles si besoin

    logo_url = request.build_absolute_uri(static('images/bckg.jpg'))

    html_string = render_to_string('classes/schoolclass_print_pdf.html', {
        'schoolclass': schoolclass,
        'students': students,
        'assigned_teachers': assigned_teachers,
        'subjects': subjects,
        'logo_url': logo_url,
        'request': request,
    })

    pdf_file = BytesIO()
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(pdf_file)
    pdf_file.seek(0)
    pdf = pdf_file.read()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=classe_{schoolclass.name}.pdf'
    return response

@login_required
def timetable_interactive(request, class_id):
    """
    Affiche l'emploi du temps interactif d'une classe sous forme de tableau (jours x créneaux horaires).
    Les créneaux sont récupérés depuis le modèle TimetableSlot.
    """
    schoolclass = get_object_or_404(SchoolClass, pk=class_id)
    year = schoolclass.year
    # Récupère tous les créneaux pour cette classe et cette année
    slots = TimetableSlot.objects.filter(class_obj=schoolclass, year=year).select_related('subject', 'teacher')
    # Structure les créneaux par jour et période pour affichage facile
    timetable = {}
    for day, _ in TimetableSlot.DAY_CHOICES:
        timetable[day] = {}
        for period in range(1, 9):  # 8 créneaux par jour par exemple
            timetable[day][period] = None
    for slot in slots:
        timetable[slot.day][slot.period] = slot

    # Définition des horaires et pauses
    horaires = [
        {'type': 'cours', 'label': '07h30 - 08h30', 'period': 1},
        {'type': 'cours', 'label': '08h30 - 09h30', 'period': 2},
        {'type': 'cours', 'label': '09h30 - 10h30', 'period': 3},
        {'type': 'pause', 'label': 'Pause (10h30 - 10h45)'},
        {'type': 'cours', 'label': '10h45 - 11h45', 'period': 4},
        {'type': 'cours', 'label': '11h45 - 12h45', 'period': 5},
        {'type': 'pause', 'label': 'Pause déjeuner (12h45 - 14h15)'},
        {'type': 'cours', 'label': '14h15 - 15h15', 'period': 6},
        {'type': 'cours', 'label': '15h15 - 16h00', 'period': 7},
    ]

    # Construction de la matrice d'affichage (table_cells)
    table_cells = []
    for idx, horaire in enumerate(horaires):
        row = {'horaire': horaire, 'cells': []}
        if horaire['type'] == 'pause':
            row['is_pause'] = True
            table_cells.append(row)
            continue
        period = horaire['period']
        for day_num, _ in TimetableSlot.DAY_CHOICES:
            slot = timetable[day_num].get(period)
            show = True
            rowspan = 1
            if slot:
                # Vérifier si ce slot a déjà été affiché plus haut (fusion verticale)
                for prev_idx in range(idx):
                    prev_horaire = horaires[prev_idx]
                    if prev_horaire['type'] == 'cours':
                        prev_period = prev_horaire['period']
                        prev_slot = timetable[day_num].get(prev_period)
                        if prev_slot and prev_slot.id == slot.id:
                            show = False
                            break
                rowspan = slot.duration if show else 1
            cell = {'slot': slot, 'show': show, 'rowspan': rowspan, 'day_num': day_num, 'period': period}
            row['cells'].append(cell)
        row['is_pause'] = False
        table_cells.append(row)

    context = {
        'schoolclass': schoolclass,
        'timetable': timetable,
        'day_choices': TimetableSlot.DAY_CHOICES,
        'horaires': horaires,
        'table_cells': table_cells,
        'is_wednesday': False,  # à utiliser dans le template si besoin
    }
    return render(request, 'classes/timetable_interactive.html', context)

def slot_add_htmx(request):
    """
    Vue pour afficher et traiter le formulaire d'ajout d'un créneau d'emploi du temps.
    """
    class_id = request.GET.get('class_id')
    year_id = request.GET.get('year_id')
    day = request.GET.get('day')
    period = request.GET.get('period')
    if request.method == 'POST':
        form = TimetableSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.class_obj_id = class_id
            slot.year_id = year_id
            slot.day = day
            slot.period = period
            slot.save()
            return JsonResponse({'success': True})
    else:
        form = TimetableSlotForm()
    return render(request, 'classes/partials/timetable_slot_form.html', {
        'form': form,
        'action': request.path + f'?class_id={class_id}&year_id={year_id}&day={day}&period={period}',
        'is_edit': False,
    })

def slot_edit_htmx(request, slot_id):
    """
    Vue pour afficher et traiter le formulaire d'édition d'un créneau d'emploi du temps.
    """
    slot = get_object_or_404(TimetableSlot, pk=slot_id)
    if request.method == 'POST':
        form = TimetableSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
    else:
        form = TimetableSlotForm(instance=slot)
    return render(request, 'classes/partials/timetable_slot_form.html', {
        'form': form,
        'action': request.path,
        'is_edit': True,
        'slot': slot,
    })

@require_POST
@csrf_exempt
def create_schoollevel_ajax(request):
    form = SchoolLevelForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@require_POST
@csrf_exempt
def assign_subjects_bulk(request):
    """
    Affecte des matières à une ou plusieurs classes et met à jour le champ subject_teached.
    Modifié le 07/07/2025 :
    - Remplit automatiquement le champ subject_teached (JSONField) de SchoolClass avec les ids des matières affectées.
    """
    # Données attendues :
    # classes: [id, ...], subjects: [id, ...], coefficients: {subject_id: coef}, hours: {subject_id: hours}, year: id
    class_ids = request.POST.getlist('classes[]')
    subject_ids = request.POST.getlist('subjects[]')
    coefficients = request.POST.get('coefficients', '{}')
    hours = request.POST.get('hours', '{}')
    year_id = request.POST.get('year')
    import json
    try:
        coefficients = json.loads(coefficients)
        hours = json.loads(hours)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Format des coefficients ou heures invalide.'}, status=400)
    year = SchoolYear.objects.get(id=year_id)
    for class_id in class_ids:
        school_class = SchoolClass.objects.get(id=class_id)
        # Affectation des matières et MAJ du champ subject_teached
        subject_id_list = []
        for subject_id in subject_ids:
            subject = Subject.objects.get(id=subject_id)
            coef = coefficients.get(str(subject_id), 1)
            h = hours.get(str(subject_id), 0)
            # Affectation sans enseignant (teacher=None)
            TeachingAssignment.objects.update_or_create(
                teacher=None,
                subject=subject,
                school_class=school_class,
                year=year,
                defaults={
                    'coefficient': coef,
                    'hours_per_week': h,
                }
            )
            subject_id_list.append(int(subject_id))
        # MAJ du champ subject_teached
        school_class.subject_teached = subject_id_list
        school_class.save(update_fields=['subject_teached'])
    return JsonResponse({'success': True})

@login_required
def assign_main_teacher_htmx(request, class_id):
    """
    Vue HTMX pour affecter ou modifier le professeur titulaire d'une classe.
    
    Cette vue gère l'affectation d'un professeur titulaire à une classe via le champ main_teacher
    du modèle SchoolClass.
    
    Args:
        request: La requête HTTP
        class_id (int): L'ID de la classe concernée
        
    Returns:
        HttpResponse: Rendu HTML pour HTMX ou redirection en cas d'erreur
    """
    try:
        # Récupération de la classe
        school_class = get_object_or_404(SchoolClass, pk=class_id)
        logger.info(f"=== DÉBUT assign_main_teacher_htmx pour la classe {school_class.name} (ID: {class_id}) ===")
        logger.info(f"Méthode HTTP: {request.method}")
        
        if request.method == 'POST':
            logger.info(f"POST reçu pour professeur titulaire de la classe {class_id}")
            logger.info(f"POST data: {dict(request.POST)}")
            
            teacher_id = request.POST.get('teacher')
            logger.info(f"Teacher ID reçu: '{teacher_id}'")
            
            try:
                if teacher_id and teacher_id.strip():
                    # Affectation d'un nouveau professeur titulaire
                    teacher = get_object_or_404(Teacher, pk=teacher_id)
                    logger.info(f"Enseignant sélectionné: {teacher.last_name} {teacher.first_name} (ID: {teacher_id})")
                    logger.info(f"Avant affectation - main_teacher: {school_class.main_teacher}")
                    
                    # Affecter directement le professeur titulaire
                    school_class.main_teacher = teacher
                    school_class.save(update_fields=['main_teacher'])
                    
                    # Recharger l'objet depuis la base de données
                    school_class.refresh_from_db()
                    logger.info(f"Après affectation - main_teacher: {school_class.main_teacher}")
                    
                    logger.info(f"Professeur titulaire affecté avec succès: {teacher} -> {school_class}")
                    
                else:
                    # Suppression du professeur titulaire
                    logger.info(f"Suppression du professeur titulaire de la classe {school_class.name}")
                    logger.info(f"Avant suppression - main_teacher: {school_class.main_teacher}")
                    
                    school_class.main_teacher = None
                    school_class.save(update_fields=['main_teacher'])
                    
                    # Recharger l'objet depuis la base de données
                    school_class.refresh_from_db()
                    logger.info(f"Après suppression - main_teacher: {school_class.main_teacher}")
                    
                    logger.info(f"Professeur titulaire supprimé avec succès de la classe {school_class.name}")
                
                # Retourner une réponse HTMX avec le nouveau contenu
                logger.info("Rendu du template main_teacher_display.html")
                
                # Récupérer les enseignants pour le contexte
                teachers = Teacher.objects.filter(
                    is_active=True, 
                    school=school_class.school, 
                    year=school_class.year
                ).order_by('last_name', 'first_name')
                
                response_html = render(request, 'classes/partials/main_teacher_display.html', {
                    'school_class': school_class,
                    'teachers': teachers
                })
                
                logger.info(f"Réponse HTML générée, longueur: {len(response_html.content)}")
                return response_html
                
            except ValueError as e:
                logger.warning(f"Erreur de validation: {str(e)}")
                return HttpResponseBadRequest(str(e))
            except Teacher.DoesNotExist:
                logger.error(f"Enseignant avec l'ID {teacher_id} non trouvé")
                return HttpResponseBadRequest("Enseignant non trouvé.")
            except Exception as e:
                logger.error(f"Erreur lors de l'affectation du professeur titulaire: {str(e)}")
                logger.exception("Traceback complet:")
                return HttpResponseBadRequest("Erreur lors de l'affectation du professeur titulaire.")
        
        # GET: Affichage du formulaire
        logger.info(f"Affichage du formulaire d'affectation du professeur titulaire pour la classe {school_class.name}")
        
        # Récupérer tous les enseignants actifs de la même école et année
        teachers = Teacher.objects.filter(
            is_active=True, 
            school=school_class.school, 
            year=school_class.year
        ).order_by('last_name', 'first_name')
        
        logger.info(f"Enseignants trouvés: {teachers.count()}")
        for teacher in teachers:
            logger.debug(f"  - {teacher.last_name} {teacher.first_name} (ID: {teacher.id})")
        
        logger.info(f"Professeur titulaire actuel: {school_class.main_teacher}")
        
        context = {
            'school_class': school_class,
            'teachers': teachers,
        }
        
        logger.info(f"Formulaire d'affectation affiché pour la classe {school_class.name} avec {teachers.count()} enseignants disponibles")
        logger.info(f"=== FIN assign_main_teacher_htmx ===")
        
        # Retourner le template de la modale
        return render(request, 'classes/partials/main_teacher_modal.html', context)
        
    except SchoolClass.DoesNotExist:
        logger.error(f"Classe avec l'ID {class_id} non trouvée")
        return HttpResponseBadRequest("Classe non trouvée.")
    except Exception as e:
        logger.error(f"Erreur inattendue dans assign_main_teacher_htmx: {str(e)}")
        logger.exception("Traceback complet:")
        return HttpResponseBadRequest("Une erreur inattendue s'est produite.")


@login_required
def update_timetable_slot(request):
    """Vue AJAX pour modifier un créneau d'emploi du temps"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        slot_id = request.POST.get('slot_id')
        day = request.POST.get('day')
        period = request.POST.get('period')
        
        if not all([slot_id, day, period]):
            return JsonResponse({'success': False, 'error': 'Tous les champs sont obligatoires'})
        
        # Récupérer le créneau
        slot = get_object_or_404(TimetableSlot, pk=slot_id)
        
        # Vérifier que le nouveau créneau n'est pas déjà occupé
        existing_slot = TimetableSlot.objects.filter(
            class_obj=slot.class_obj,
            day=day,
            period=period,
            year=slot.class_obj.year
        ).exclude(pk=slot_id).first()
        
        if existing_slot:
            return JsonResponse({
                'success': False, 
                'error': f'Le créneau {existing_slot.get_day_display()} {existing_slot.get_period_display()} est déjà occupé par {existing_slot.subject.name}'
            })
        
        # Mettre à jour le créneau
        slot.day = int(day)
        slot.period = int(period)
        slot.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Créneau modifié avec succès'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erreur: {str(e)}'})


@login_required
def delete_timetable_slot(request):
    """Vue AJAX pour supprimer un créneau d'emploi du temps"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        slot_id = request.POST.get('slot_id')
        
        if not slot_id:
            return JsonResponse({'success': False, 'error': 'ID du créneau manquant'})
        
        # Récupérer et supprimer le créneau
        slot = get_object_or_404(TimetableSlot, pk=slot_id)
        subject_name = slot.subject.name
        slot.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'Créneau {subject_name} supprimé avec succès'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erreur: {str(e)}'})
