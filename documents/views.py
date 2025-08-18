from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.db.models import Q
from .models import StudentDocument, DocumentCategory
from .forms import StudentDocumentForm
from students.models import Student

@login_required
def document_list(request, student_id):
    """Liste des documents d'un étudiant"""
    student = get_object_or_404(Student, pk=student_id)
    documents = StudentDocument.objects.filter(student=student).select_related('category')
    categories = DocumentCategory.objects.all()
    
    context = {
        'student': student,
        'documents': documents,
        'categories': categories,
    }
    return render(request, 'documents/document_list.html', context)

@login_required
def document_create(request, student_id):
    """Créer un nouveau document"""
    student = get_object_or_404(Student, pk=student_id)
    
    if request.method == 'POST':
        form = StudentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.student = student
            document.uploaded_by = request.user
            document.save()
            
            if request.headers.get('HX-Request'):
                # Retourner le HTML pour HTMX
                documents = StudentDocument.objects.filter(student=student).select_related('category')
                html = render_to_string('documents/partials/document_list.html', {
                    'documents': documents
                }, request=request)
                return HttpResponse(html)
            else:
                messages.success(request, 'Document ajouté avec succès.')
                return redirect('documents:document_list', student_id=student_id)
    else:
        form = StudentDocumentForm(initial={'student': student})
    
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'documents/document_form.html', context)

@login_required
def document_update(request, pk):
    """Modifier un document"""
    document = get_object_or_404(StudentDocument, pk=pk)
    
    if request.method == 'POST':
        form = StudentDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            
            if request.headers.get('HX-Request'):
                # Retourner le HTML pour HTMX
                documents = StudentDocument.objects.filter(student=document.student).select_related('category')
                html = render_to_string('documents/partials/document_list.html', {
                    'documents': documents
                }, request=request)
                return HttpResponse(html)
            else:
                messages.success(request, 'Document modifié avec succès.')
                return redirect('documents:document_list', student_id=document.student.pk)
    else:
        form = StudentDocumentForm(instance=document)
    
    context = {
        'form': form,
        'document': document,
        'student': document.student,
    }
    return render(request, 'documents/document_form.html', context)

@login_required
def document_delete(request, pk):
    """Supprimer un document"""
    document = get_object_or_404(StudentDocument, pk=pk)
    student_id = document.student.pk
    
    if request.method == 'POST':
        document.delete()
        
        if request.headers.get('HX-Request'):
            # Retourner le HTML pour HTMX
            documents = StudentDocument.objects.filter(student_id=student_id).select_related('category')
            html = render_to_string('documents/partials/document_list.html', {
                'documents': documents
            }, request=request)
            return HttpResponse(html)
        else:
            messages.success(request, 'Document supprimé avec succès.')
            return redirect('documents:document_list', student_id=student_id)
    
    context = {
        'document': document,
        'student': document.student,
    }
    return render(request, 'documents/document_confirm_delete.html', context)

@login_required
def document_download(request, pk):
    """Télécharger un document"""
    document = get_object_or_404(StudentDocument, pk=pk)
    
    # Vérifier les permissions si nécessaire
    # if not request.user.has_perm('documents.download_document'):
    #     messages.error(request, 'Vous n\'avez pas la permission de télécharger ce document.')
    #     return redirect('documents:document_list', student_id=document.student.pk)
    
    response = HttpResponse(document.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.title}{document.file_extension}"'
    return response

@login_required
def document_search(request, student_id):
    """Rechercher des documents"""
    student = get_object_or_404(Student, pk=student_id)
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    documents = StudentDocument.objects.filter(student=student).select_related('category')
    
    if query:
        documents = documents.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    if category_id:
        documents = documents.filter(category_id=category_id)
    
    context = {
        'student': student,
        'documents': documents,
        'query': query,
        'selected_category': category_id,
    }
    
    if request.headers.get('HX-Request'):
        html = render_to_string('documents/partials/document_list.html', context, request=request)
        return HttpResponse(html)
    
    return render(request, 'documents/document_list.html', context)
