from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import TeachingAssignment, Teacher
from .forms import TeachingAssignmentForm, TeacherForm, TeachingAssignmentCoefForm
from classes.models import SchoolClass
from school.models import SchoolYear
from subjects.models import Subject
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

# 07/07/2025 - Vue universelle pour création d'affectation, renvoie le formulaire HTML pour la modale universelle

def teaching_assignment_create_htmx(request, class_id):
    """
    Crée une affectation matière-enseignant pour une classe (modale universelle)
    Refonte du 07/07/2025
    """
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    year = school_class.year
    if request.method == 'POST':
        form = TeachingAssignmentForm(request.POST)
        if form.is_valid():
            # Créer l'affectation
            assignment = form.save()
            
            # Mettre à jour le champ subject_teached de la classe
            subject_ids = school_class.subject_teached or []
            if assignment.subject.id not in subject_ids:
                subject_ids.append(assignment.subject.id)
                school_class.subject_teached = subject_ids
                school_class.save(update_fields=['subject_teached'])
            
            return HttpResponse(status=204)
        else:
            # Retourner le formulaire avec les erreurs
            return render(request, 'teachers/teaching_assignment_modal_form.html', {
                'form': form,
                'school_class': school_class,
                'context_title': f"Affecter une matière à {school_class.name}",
                'context_info': f"Année : {year}",
                'errors': form.errors
            })
    else:
        form = TeachingAssignmentForm(initial={'school_class': school_class, 'year': year})
    
    context = {
        'form': form,
        'school_class': school_class,
        'context_title': f"Affecter une matière à {school_class.name}",
        'context_info': f"Année : {year}",
    }
    return render(request, 'teachers/teaching_assignment_modal_form.html', context)

# 07/07/2025 - Vue universelle pour modification d'affectation, renvoie le formulaire HTML pour la modale universelle

def teaching_assignment_update_htmx(request, pk):
    """
    Modifie une affectation matière-enseignant pour une classe (modale universelle)
    Refonte du 07/07/2025
    """
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    if request.method == 'POST':
        form = TeachingAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204)
    else:
        form = TeachingAssignmentForm(instance=assignment)
    context = {
        'form': form,
        'school_class': assignment.school_class,
        'context_title': f"Modifier l'affectation : {assignment.subject} ({assignment.school_class.name})",
        'context_info': f"Enseignant : {assignment.teacher} | Année : {assignment.year}",
    }
    return render(request, 'teachers/teaching_assignment_modal_form.html', context)

def teaching_assignment_full_update_htmx(request, pk):
    """
    Vue pour modifier complètement une affectation matière-enseignant (y compris l'enseignant)
    """
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    if request.method == 'POST':
        print(f"DEBUG: POST reçu pour TA {pk}")
        print(f"DEBUG: POST data: {request.POST}")
        print(f"DEBUG: Avant modification - teacher={assignment.teacher}")
        
        form = TeachingAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            print(f"DEBUG: Formulaire valide")
            print(f"DEBUG: teacher dans form.cleaned_data: {form.cleaned_data.get('teacher')}")
            
            # Sauvegarder
            updated_assignment = form.save()
            print(f"DEBUG: Après sauvegarde - teacher={updated_assignment.teacher}")
            
            return HttpResponse(status=204)
        else:
            print(f"DEBUG: Formulaire invalide - erreurs: {form.errors}")
            # Retourner le formulaire avec les erreurs
            return render(request, 'teachers/teaching_assignment_modal_form.html', {
                'form': form,
                'assignment': assignment,
                'context_title': f"Modifier l'affectation : {assignment.subject.name}",
                'context_info': f"Classe : {assignment.school_class.name} | Année : {assignment.year}",
                'errors': form.errors
            })
    else:
        form = TeachingAssignmentForm(instance=assignment)
    
    context = {
        'form': form,
        'assignment': assignment,
        'context_title': f"Modifier l'affectation : {assignment.subject.name}",
        'context_info': f"Classe : {assignment.school_class.name} | Année : {assignment.year}",
    }
    return render(request, 'teachers/teaching_assignment_modal_form.html', context)

# Suppression d'une affectation (htmx)
def teaching_assignment_delete_htmx(request, pk):
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    if request.method == 'POST':
        assignment.delete()
        return HttpResponse(status=204)
    context = {
        'assignment': assignment,
    }
    return render(request, 'teachers/teaching_assignment_delete_modal_form.html', context)

# Vue HTMX pour le select enseignant filtré selon la matière
@require_GET
def teacher_select_for_subject_htmx(request):
    subject_id = request.GET.get('subject_id')
    class_id = request.GET.get('class_id')
    form = TeachingAssignmentForm(subject_id=subject_id)
    return render(request, 'teachers/partials/teacher_select_field.html', {'form': form})

@require_POST
def teaching_assignment_update_titulaire_htmx(request, pk):
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    # Retirer le statut titulaire à tous les autres pour cette classe/année
    TeachingAssignment.objects.filter(
        school_class=assignment.school_class,
        year=assignment.year,
        is_titulaire=True
    ).exclude(pk=assignment.pk).update(is_titulaire=False)
    # Mettre à jour ce prof comme titulaire
    assignment.is_titulaire = True
    assignment.save()
    return HttpResponse(status=204)

def teacher_list(request):
    teachers = Teacher.objects.select_related('school', 'year', 'main_subject').all()
    subjects = Subject.objects.all()
    # Gestion des filtres (exemple simple)
    subject_id = request.GET.get('subject')
    if subject_id and subject_id != 'all':
        teachers = teachers.filter(assignments__subject_id=subject_id).distinct()
    # Toast de succès si présent dans la session
    toast = request.session.pop('toast', None)
    return render(request, 'teachers/teacher_list.html', {
        'teachers': teachers,
        'subjects': subjects,
        'toast': toast,
    })

def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    # Calculs additionnels pour le template (ex: nombre de matières, classes, années d'expérience)
    subjects = Subject.objects.filter(assignments__teacher=teacher).distinct()
    classes = SchoolClass.objects.filter(assignments__teacher=teacher).distinct()
    experience_years = teacher.created_at.year if teacher.created_at else 0
    # Toast de succès si présent dans la session
    toast = request.session.pop('toast', None)
    return render(request, 'teachers/teacher_detail.html', {
        'teacher': teacher,
        'subjects': subjects,
        'classes': classes,
        'experience_years': experience_years,
        'toast': toast,
    })

def teacher_create_htmx(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save()
            return JsonResponse({'success': True, 'redirect_url': f"/teachers/{teacher.pk}/", 'message': 'Enseignant ajouté avec succès.'})
    else:
        form = TeacherForm()
    html = f'''
    <div class="w-full max-w-2xl mx-auto">
        <div class="mb-6">
            <h2 class="text-2xl font-bold text-slate-900 mb-1">Ajouter un enseignant</h2>
            <p class="text-slate-500 text-sm">Remplissez les informations de l'enseignant. Tous les champs marqués d'une * sont obligatoires.</p>
        </div>
        <form method="post" enctype="multipart/form-data" hx-post="{request.path}" hx-target="#modal-content" hx-swap="innerHTML" class="space-y-6">
            {request.csrf_processing_done and '' or f'<input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get("CSRF_COOKIE", "")}" />'}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {''.join([f'<div><label for="{field.id_for_label}" class="block text-slate-700 font-medium mb-1">{field.label}{"<span class=\"text-red-500\">*</span>" if field.field.required else ""}</label>{field.as_widget(attrs={"class": "w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"})}{f"<div class=\"text-xs text-slate-400 mt-1\">{field.help_text}</div>" if field.help_text else ""}{f"<div class=\"text-red-600 text-xs mt-1\">{''.join([str(e) for e in field.errors])}</div>" if field.errors else ""}</div>' for field in form.visible_fields()])}
            </div>
            <div class="flex justify-end gap-2 pt-4 border-t border-slate-100 mt-6">
                <button type="button" onclick="document.getElementById('modal-overlay').classList.add('hidden')" class="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors duration-200">Annuler</button>
                <button type="submit" class="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"><i class="fas fa-save mr-2"></i>Enregistrer</button>
            </div>
        </form>
    </div>
    '''
    return HttpResponse(mark_safe(html))

def teacher_update_htmx(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'redirect_url': f"/teachers/{teacher.pk}/", 'message': 'Enseignant modifié avec succès.'})
    else:
        form = TeacherForm(instance=teacher)
    html = f'''
    <div class="w-full max-w-2xl mx-auto">
        <div class="mb-6">
            <h2 class="text-2xl font-bold text-slate-900 mb-1">Modifier un enseignant</h2>
            <p class="text-slate-500 text-sm">Modifiez les informations de l'enseignant. Tous les champs marqués d'une * sont obligatoires.</p>
        </div>
        <form method="post" enctype="multipart/form-data" hx-post="{request.path}" hx-target="#modal-content" hx-swap="innerHTML" class="space-y-6">
            {request.csrf_processing_done and '' or f'<input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get("CSRF_COOKIE", "")}" />'}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {''.join([f'<div><label for="{field.id_for_label}" class="block text-slate-700 font-medium mb-1">{field.label}{"<span class=\"text-red-500\">*</span>" if field.field.required else ""}</label>{field.as_widget(attrs={"class": "w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"})}{f"<div class=\"text-xs text-slate-400 mt-1\">{field.help_text}</div>" if field.help_text else ""}{f"<div class=\"text-red-600 text-xs mt-1\">{''.join([str(e) for e in field.errors])}</div>" if field.errors else ""}</div>' for field in form.visible_fields()])}
            </div>
            <div class="flex justify-end gap-2 pt-4 border-t border-slate-100 mt-6">
                <button type="button" onclick="document.getElementById('modal-overlay').classList.add('hidden')" class="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors duration-200">Annuler</button>
                <button type="submit" class="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"><i class="fas fa-save mr-2"></i>Enregistrer</button>
            </div>
        </form>
    </div>
    '''
    return HttpResponse(mark_safe(html))

def teacher_delete_htmx(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.delete()
        return JsonResponse({'success': True, 'redirect_url': '/teachers/', 'message': 'Enseignant supprimé avec succès.'})
    html = f'''
    <div class="w-full max-w-lg mx-auto">
        <div class="mb-6">
            <h2 class="text-xl font-bold text-red-700 mb-1">Confirmer la suppression</h2>
            <p class="text-slate-500 text-sm">Voulez-vous vraiment supprimer l'enseignant <span class="font-semibold">{teacher.first_name} {teacher.last_name}</span> ? Cette action est irréversible.</p>
        </div>
        <form method="post" hx-post="{request.path}" hx-target="#modal-content" hx-swap="innerHTML" class="space-y-6">
            {request.csrf_processing_done and '' or f'<input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get("CSRF_COOKIE", "")}" />'}
            <div class="flex justify-end gap-2 pt-4 border-t border-slate-100 mt-6">
                <button type="button" onclick="document.getElementById('modal-overlay').classList.add('hidden')" class="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors duration-200">Annuler</button>
                <button type="submit" class="px-6 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-xl hover:from-red-700 hover:to-amber-700 transition-all duration-200 shadow-lg hover:shadow-xl"><i class="fas fa-trash mr-2"></i>Supprimer</button>
            </div>
        </form>
    </div>
    '''
    return HttpResponse(mark_safe(html))

@require_http_methods(["GET", "POST"])
def teacher_assign_subjects_htmx(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    all_subjects = Subject.objects.all()
    if request.method == "POST":
        subject_ids = request.POST.getlist("subjects")
        for subject in all_subjects:
            if str(subject.id) in subject_ids:
                subject.teachers.add(teacher)
            else:
                subject.teachers.remove(teacher)
        assigned_subject_ids = [int(s) for s in subject_ids]
        success = True
    else:
        assigned_subject_ids = list(teacher.subjects.all().values_list("id", flat=True))
        success = False

    html = f'''
    <div class="w-full max-w-lg mx-auto">
        <div class="mb-6">
            <h2 class="text-xl font-bold text-slate-900 mb-1">Affecter des matières</h2>
            <p class="text-slate-500 text-sm">Sélectionnez les matières à affecter à ce professeur.</p>
        </div>
        <form method="post" hx-post="{request.path}" hx-target="#modal-content" hx-swap="innerHTML" class="space-y-6">
            {request.csrf_processing_done and '' or f'<input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get("CSRF_COOKIE", "")}" />'}
            <div class="mb-4">
                <label for="subjects" class="block text-slate-700 font-medium mb-2">Matières enseignées</label>
                <select name="subjects" id="subjects" multiple class="w-full border border-slate-300 rounded-lg px-3 py-2">
                    {''.join([f'<option value="{subject.id}" {"selected" if subject.id in assigned_subject_ids else ""}>{subject.name}</option>' for subject in all_subjects])}
                </select>
            </div>
            <div class="flex justify-end gap-2 pt-4 border-t border-slate-100 mt-6">
                <button type="button" onclick="document.getElementById('modal-overlay').classList.add('hidden')" class="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors duration-200">Annuler</button>
                <button type="submit" class="px-6 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl">
                    <i class="fas fa-save mr-2"></i>Enregistrer
                </button>
            </div>
        </form>
        <div class="mt-6">
            <h4 class="font-semibold text-slate-800 mb-2">Matières actuellement affectées :</h4>
            <ul class="list-disc pl-6 text-slate-700">
                {''.join([f'<li>{subject.name}</li>' for subject in teacher.subjects.all()]) or '<li class="text-slate-400">Aucune matière affectée.</li>'}
            </ul>
        </div>
        {'<div class="mt-4 text-green-600 font-semibold">Affectation mise à jour avec succès !</div>' if success else ''}
    </div>
    '''
    return HttpResponse(mark_safe(html))

@require_http_methods(["GET", "POST"])
def teacher_assign_classes_htmx(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    all_classes = SchoolClass.objects.all()
    if request.method == "POST":
        class_ids = request.POST.getlist("classes")
        # Supprimer les affectations non sélectionnées
        teacher.assignments.exclude(school_class_id__in=class_ids).delete()
        # Ajouter les nouvelles affectations
        for class_id in class_ids:
            SchoolClass.objects.get(pk=class_id).assignments.get_or_create(teacher=teacher, year=teacher.year)
        assigned_class_ids = [int(c) for c in class_ids]
        return render(request, "teachers/partials/teacher_classes_form.html", {
            "teacher": teacher,
            "classes": all_classes,
            "assigned_class_ids": assigned_class_ids,
            "success": True,
        })
    assigned_class_ids = list(teacher.assignments.values_list("school_class_id", flat=True))
    return render(request, "teachers/partials/teacher_classes_form.html", {
        "teacher": teacher,
        "classes": all_classes,
        "assigned_class_ids": assigned_class_ids,
    })

def teaching_assignment_coef_update_htmx(request, pk):
    assignment = get_object_or_404(TeachingAssignment, pk=pk)
    if request.method == 'POST':
        form = TeachingAssignmentCoefForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204)
    else:
        form = TeachingAssignmentCoefForm(instance=assignment)
    context = {
        'form': form,
        'assignment': assignment,
    }
    return render(request, 'teachers/teaching_assignment_coef_modal_form.html', context)

@csrf_exempt
def teaching_assignment_bulk_delete_htmx(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        TeachingAssignment.objects.filter(id__in=ids).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
