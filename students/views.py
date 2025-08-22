from django.shortcuts import render
from django.views.generic import ListView, View
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db import models
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from authentication.permissions import TeacherPermissionManager, require_teacher_assignment
from .models import Student, StudentClassHistory, Guardian, StudentDocument, Scholarship
from .forms import StudentForm
from school.models import SchoolYear
from classes.models import SchoolClass
from teachers.models import Teacher
from django.urls import reverse_lazy
from finances.models import TranchePayment, FeeDiscount, PaymentRefund, ExtraFee, FeeStructure
from students.models import Evaluation, Attendance, Sanction
from django.http import JsonResponse
from .forms import GuardianForm

# Vue pour afficher la liste des élèves
class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = "students/students_list.html"
    context_object_name = "students"
    paginate_by = 25  # Valeur par défaut

    def get_paginate_by(self, queryset):
        """Permet de changer dynamiquement le nombre d'éléments par page"""
        return self.request.GET.get('page_size', self.paginate_by)

    def get_queryset(self):
        # Vérifier les permissions du professeur
        if self.request.user.role == 'PROFESSEUR':
            require_teacher_assignment(self.request.user)
            permission_manager = TeacherPermissionManager(self.request.user)
        
        queryset = Student.objects.select_related('current_class', 'year', 'school').all()
        
        # Filtrer selon les permissions du professeur
        if self.request.user.role == 'PROFESSEUR':
            queryset = permission_manager.filter_queryset_students(queryset)
            # Si aucun étudiant accessible, afficher un message d'information
            if not queryset.exists():
                # Lever une exception avec un message informatif
                assignment_info = permission_manager.get_assignment_info()
                if not assignment_info['has_assignments']:
                    raise PermissionDenied(
                        "Vous n'avez pas encore été assigné à des classes. "
                        "Contactez l'administration pour obtenir vos assignations."
                    )
                else:
                    raise PermissionDenied(
                        "Aucun étudiant trouvé dans vos classes assignées."
                    )
        
        # Filtre par classe (filtré selon les permissions)
        classe = self.request.GET.get('class')
        if classe and classe != 'all':
            # Vérifier si le professeur peut accéder à cette classe
            if self.request.user.role == 'PROFESSEUR':
                if not permission_manager.can_access_class(int(classe)):
                    raise PermissionDenied("Vous n'avez pas accès à cette classe.")
            queryset = queryset.filter(current_class_id=classe)
        
        # Filtre par année scolaire
        year = self.request.GET.get('year')
        if year and year != 'all':
            queryset = queryset.filter(year_id=year)
        
        # Filtre par statut actif/inactif
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Recherche par nom, prénom ou matricule
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(matricule__icontains=search)
            )
        
        # Tri par défaut
        order_by = self.request.GET.get('order_by', 'last_name')
        direction = self.request.GET.get('direction', 'asc')
        
        if direction == 'desc':
            order_by = f'-{order_by}'
        
        queryset = queryset.order_by(order_by)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer tous les paramètres de filtrage
        context['current_filters'] = {
            'class': self.request.GET.get('class', ''),
            'year': self.request.GET.get('year', ''),
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
            'order_by': self.request.GET.get('order_by', 'last_name'),
            'direction': self.request.GET.get('direction', 'asc'),
            'page_size': self.request.GET.get('page_size', '25'),
        }
        
        # Filtrer les options selon les permissions du professeur
        if self.request.user.role == 'PROFESSEUR':
            permission_manager = TeacherPermissionManager(self.request.user)
            accessible_class_ids = permission_manager.get_accessible_classes()
            context['classes'] = SchoolClass.objects.filter(id__in=accessible_class_ids).order_by('name')
            
            # Statistiques limitées aux classes accessibles
            student_queryset = permission_manager.filter_queryset_students(Student.objects.all())
            total_students = student_queryset.count()
            active_students = student_queryset.filter(is_active=True).count()
            inactive_students = student_queryset.filter(is_active=False).count()
            
            # Informations sur les assignations
            assignment_info = permission_manager.get_assignment_info()
            context['assignment_info'] = assignment_info
        else:
            # Pour les non-professeurs, afficher toutes les classes
            context['classes'] = SchoolClass.objects.all().order_by('name')
            
            # Statistiques globales
            total_students = Student.objects.count()
            active_students = Student.objects.filter(is_active=True).count()
            inactive_students = Student.objects.filter(is_active=False).count()
        
        context['years'] = SchoolYear.objects.all().order_by('-annee')
        
        context['stats'] = {
            'total': total_students,
            'active': active_students,
            'inactive': inactive_students,
        }
        
        # Variables pour le sidebar (compatibilité avec le template)
        context['students_count'] = total_students
        context['teachers_count'] = Teacher.objects.filter(is_active=True).count()
        context['classes_count'] = SchoolClass.objects.filter(is_active=True).count()
        
        return context

# Vues HTMX pour créer, modifier et supprimer un élève via des modales

class StudentCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = StudentForm()
        context = {"form": form}
        html = render_to_string("students/partials/student_form.html", context, request=request)
        return HttpResponse(html)

    def post(self, request, *args, **kwargs):
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            students = Student.objects.all()
            classes = SchoolClass.objects.all()
            years = SchoolYear.objects.all()
            context = {"students": students, "classes": classes, "years": years}
            return render(request, "students/students_list.html", context)
        else:
            html = render_to_string("students/partials/student_form.html", {"form": form}, request=request)
            return HttpResponse(html)

class StudentUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk)
        form = StudentForm(instance=student)
        context = {"form": form, "student": student}
        html = render_to_string("students/partials/student_form.html", context, request=request)
        return HttpResponse(html)

    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk)
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            students = Student.objects.all()
            classes = SchoolClass.objects.all()
            years = SchoolYear.objects.all()
            context = {"students": students, "classes": classes, "years": years}
            return render(request, "students/students_list.html", context)
        else:
            html = render_to_string("students/partials/student_form.html", {"form": form, "student": student}, request=request)
            return HttpResponse(html)

class StudentDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk)
        html = render_to_string("students/partials/student_confirm_delete.html", {"student": student}, request=request)
        return HttpResponse(html)

    def post(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk)
        student.delete()
        students = Student.objects.all()
        classes = SchoolClass.objects.all()
        years = SchoolYear.objects.all()
        context = {"students": students, "classes": classes, "years": years}
        return render(request, "students/students_list.html", context)

# Vues utilitaires pour filtrer les élèves (HTMX)
def filter_students(request):
    """
    Vue utilitaire pour filtrer les élèves selon la classe, l'année scolaire, l'état (actif/inactif), etc.
    Utilisée par HTMX.
    """
    classe = request.GET.get('class')
    year = request.GET.get('year')
    is_active = request.GET.get('is_active')

    students = Student.objects.all()
    if classe:
        students = students.filter(current_class_id=classe)
    if year:
        students = students.filter(year_id=year)
    if is_active is not None:
        students = students.filter(is_active=is_active)

    classes = SchoolClass.objects.all()
    years = SchoolYear.objects.all()
    context = {"students": students, "classes": classes, "years": years}
    return render(request, "students/students_list.html", context)

class StudentDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        student = get_object_or_404(Student, pk=pk)
        
        # Récupérer tous les éléments liés
        history = StudentClassHistory.objects.filter(student=student).order_by('-year')
        guardians = Guardian.objects.filter(student=student)
        documents = StudentDocument.objects.filter(student=student)
        scholarships = Scholarship.objects.filter(student=student)
        evaluations = Evaluation.objects.filter(student=student)
        attendances = Attendance.objects.filter(student=student)
        sanctions = Sanction.objects.filter(student=student)
        
        # Récupérer les paiements avec les relations
        payments = TranchePayment.objects.filter(student=student).select_related(
            'tranche', 'tranche__fee_structure', 'tranche__fee_structure__year'
        ).order_by('-payment_date')
        
        # Calculer les statistiques financières
        total_paid = payments.aggregate(total=models.Sum('amount'))['total'] or 0
        
        # Récupérer les structures de frais de la classe actuelle
        if student.current_class:
            fee_structures = FeeStructure.objects.filter(school_class=student.current_class)
            total_due = 0
            for fs in fee_structures:
                total_due += fs.tuition_total
            
            # Calculer le pourcentage payé
            payment_percentage = (total_paid / total_due * 100) if total_due > 0 else 0
            remaining_amount = total_due - total_paid
        else:
            total_due = 0
            payment_percentage = 0
            remaining_amount = 0
        
        # Récupérer l'activité récente (derniers 10 événements)
        from django.db.models import Q
        from datetime import datetime, timedelta
        
        # Activité récente : paiements, évaluations, présences, sanctions
        recent_activities = []
        
        # Paiements récents
        recent_payments = payments[:3]
        for payment in recent_payments:
            recent_activities.append({
                'type': 'payment',
                'title': f'Paiement reçu - {payment.amount:.0f} FCFA',
                'description': f'{"Tranche " + str(payment.tranche.number) if payment.tranche else "Frais d\'inscription"} - {payment.get_mode_display}',
                'date': payment.payment_date,
                'icon': 'fas fa-money-bill',
                'color': 'emerald',
                'time_ago': self._get_time_ago(payment.payment_date)
            })
        
        # Évaluations récentes
        recent_evaluations = evaluations.order_by('-created_at')[:3]
        for evaluation in recent_evaluations:
            recent_activities.append({
                'type': 'evaluation',
                'title': f'Note ajoutée en {evaluation.subject.name}',
                'description': f'{evaluation.score}/{evaluation.max_score} - {evaluation.get_sequence_display()}',
                'date': evaluation.created_at.date(),
                'icon': 'fas fa-book',
                'color': 'blue',
                'time_ago': self._get_time_ago(evaluation.created_at.date())
            })
        
        # Présences récentes (absences/retards)
        recent_attendances = attendances.filter(present=False).order_by('-date')[:3]
        for attendance in recent_attendances:
            recent_activities.append({
                'type': 'attendance',
                'title': 'Absence signalée',
                'description': attendance.reason or 'Absence non justifiée',
                'date': attendance.date,
                'icon': 'fas fa-clock',
                'color': 'amber',
                'time_ago': self._get_time_ago(attendance.date)
            })
        
        # Sanctions récentes
        recent_sanctions = sanctions.order_by('-date')[:3]
        for sanction in recent_sanctions:
            recent_activities.append({
                'type': 'sanction',
                'title': f'Sanction : {sanction.sanction_type}',
                'description': sanction.reason[:50] + '...' if len(sanction.reason) > 50 else sanction.reason,
                'date': sanction.date,
                'icon': 'fas fa-exclamation-triangle',
                'color': 'red',
                'time_ago': self._get_time_ago(sanction.date)
            })
        
        # Trier par date (plus récent en premier)
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        recent_activities = recent_activities[:10]
        
        # Récupérer les documents de l'app documents
        try:
            from documents.models import StudentDocument as DocStudentDocument
            student_documents = DocStudentDocument.objects.filter(student=student).select_related('category').order_by('-uploaded_at')
        except:
            student_documents = []
        
        context = {
            'student': student,
            'history': history,
            'guardians': guardians,
            'documents': documents,
            'student_documents': student_documents,
            'payments': payments,
            'scholarships': scholarships,
            'evaluations': evaluations,
            'attendances': attendances,
            'sanctions': sanctions,
            'total_paid': total_paid,
            'total_due': total_due,
            'payment_percentage': payment_percentage,
            'remaining_amount': remaining_amount,
            'recent_activities': recent_activities,
        }
        return render(request, "students/student_detail.html", context)
    
    def _get_time_ago(self, date):
        """Convertit une date en format 'il y a X temps'"""
        from datetime import date as date_class
        from datetime import datetime
        
        if isinstance(date, datetime):
            date = date.date()
        
        today = date_class.today()
        delta = today - date
        
        if delta.days == 0:
            return "Aujourd'hui"
        elif delta.days == 1:
            return "Hier"
        elif delta.days < 7:
            return f"Il y a {delta.days} jours"
        elif delta.days < 30:
            weeks = delta.days // 7
            return f"Il y a {weeks} semaine{'s' if weeks > 1 else ''}"
        elif delta.days < 365:
            months = delta.days // 30
            return f"Il y a {months} mois"
        else:
            years = delta.days // 365
            return f"Il y a {years} an{'s' if years > 1 else ''}"

class StudentHistoryCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        from .forms import StudentClassHistoryForm
        form = StudentClassHistoryForm(initial={'student': student_id})
        context = {'form': form, 'student_id': student_id}
        html = render_to_string('students/partials/history_form.html', context, request=request)
        return HttpResponse(html)
    def post(self, request, student_id, *args, **kwargs):
        from .forms import StudentClassHistoryForm
        form = StudentClassHistoryForm(request.POST)
        if form.is_valid():
            form.save()
            student = get_object_or_404(Student, pk=student_id)
            history = StudentClassHistory.objects.filter(student=student).order_by('-year')
            html = render_to_string('students/partials/history_list.html', {'history': history}, request=request)
            return HttpResponse(html)
        else:
            context = {'form': form, 'student_id': student_id}
            html = render_to_string('students/partials/history_form.html', context, request=request)
            return HttpResponse(html)

class StudentHistoryUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        from .forms import StudentClassHistoryForm
        history = get_object_or_404(StudentClassHistory, pk=pk)
        form = StudentClassHistoryForm(instance=history)
        context = {'form': form, 'history': history}
        html = render_to_string('students/partials/history_form.html', context, request=request)
        return HttpResponse(html)
    def post(self, request, pk, *args, **kwargs):
        from .forms import StudentClassHistoryForm
        history = get_object_or_404(StudentClassHistory, pk=pk)
        form = StudentClassHistoryForm(request.POST, instance=history)
        if form.is_valid():
            form.save()
            student = history.student
            history_list = StudentClassHistory.objects.filter(student=student).order_by('-year')
            html = render_to_string('students/partials/history_list.html', {'history': history_list}, request=request)
            return HttpResponse(html)
        else:
            context = {'form': form, 'history': history}
            html = render_to_string('students/partials/history_form.html', context, request=request)
            return HttpResponse(html)

class StudentHistoryDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        history = get_object_or_404(StudentClassHistory, pk=pk)
        context = {'history': history}
        html = render_to_string('students/partials/history_confirm_delete.html', context, request=request)
        return HttpResponse(html)
    def post(self, request, pk, *args, **kwargs):
        history = get_object_or_404(StudentClassHistory, pk=pk)
        student = history.student
        history.delete()
        history_list = StudentClassHistory.objects.filter(student=student).order_by('-year')
        html = render_to_string('students/partials/history_list.html', {'history': history_list}, request=request)
        return HttpResponse(html)

# --- Squelettes minimaux pour tous les modules liés à l'élève ---

# Guardians
class GuardianCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        student = get_object_or_404(Student, pk=student_id)
        form = GuardianForm(initial={'student': student})
        context = {"form": form, "student": student, "action": "create"}
        html = render_to_string("students/partials/guardian_form.html", context, request=request)
        return HttpResponse(html)
    
    def post(self, request, student_id, *args, **kwargs):
        student = get_object_or_404(Student, pk=student_id)
        form = GuardianForm(request.POST)
        if form.is_valid():
            guardian = form.save(commit=False)
            guardian.student = student
            guardian.save()
            
            # Retourner un message de succès
            context = {"student": student, "message": "Parent ajouté avec succès !"}
            html = render_to_string("students/partials/guardian_success.html", context, request=request)
            return HttpResponse(html)
        else:
            context = {"form": form, "student": student, "action": "create"}
            html = render_to_string("students/partials/guardian_form.html", context, request=request)
            return HttpResponse(html)

class GuardianUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        guardian = get_object_or_404(Guardian, pk=pk)
        form = GuardianForm(instance=guardian)
        context = {"form": form, "guardian": guardian, "student": guardian.student, "action": "update"}
        html = render_to_string("students/partials/guardian_form.html", context, request=request)
        return HttpResponse(html)
    
    def post(self, request, pk, *args, **kwargs):
        guardian = get_object_or_404(Guardian, pk=pk)
        form = GuardianForm(request.POST, instance=guardian)
        if form.is_valid():
            form.save()
            
            # Retourner un message de succès
            context = {"student": guardian.student, "message": "Parent modifié avec succès !"}
            html = render_to_string("students/partials/guardian_success.html", context, request=request)
            return HttpResponse(html)
        else:
            context = {"form": form, "guardian": guardian, "student": guardian.student, "action": "update"}
            html = render_to_string("students/partials/guardian_form.html", context, request=request)
            return HttpResponse(html)

class GuardianDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        guardian = get_object_or_404(Guardian, pk=pk)
        context = {"guardian": guardian, "student": guardian.student}
        html = render_to_string("students/partials/guardian_confirm_delete.html", context, request=request)
        return HttpResponse(html)
    
    def post(self, request, pk, *args, **kwargs):
        guardian = get_object_or_404(Guardian, pk=pk)
        student = guardian.student
        guardian.delete()
        
        # Retourner un message de succès
        context = {"student": student, "message": "Parent supprimé avec succès !"}
        html = render_to_string("students/partials/guardian_success.html", context, request=request)
        return HttpResponse(html)

# Documents
class DocumentCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        # TODO: Afficher le formulaire d'ajout de document
        pass
    def post(self, request, student_id, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class DocumentUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher le formulaire de modification
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class DocumentDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher la confirmation de suppression
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la suppression
        pass

# TranchePayment
class TranchePaymentCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        # TODO: Afficher le formulaire d'ajout de paiement
        pass
    def post(self, request, student_id, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class TranchePaymentUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher le formulaire de modification
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class TranchePaymentDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher la confirmation de suppression
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la suppression
        pass

# FeeDiscount
class FeeDiscountCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        # TODO: Afficher le formulaire d'ajout de remise
        pass
    def post(self, request, student_id, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class FeeDiscountUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher le formulaire de modification
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class FeeDiscountDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher la confirmation de suppression
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la suppression
        pass

# Scholarship
class ScholarshipCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        # TODO: Afficher le formulaire d'ajout de bourse
        pass
    def post(self, request, student_id, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class ScholarshipUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher le formulaire de modification
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class ScholarshipDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher la confirmation de suppression
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la suppression
        pass

# Evaluation
class EvaluationCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        # TODO: Afficher le formulaire d'ajout d'évaluation
        pass
    def post(self, request, student_id, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class EvaluationUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher le formulaire de modification
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class EvaluationDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher la confirmation de suppression
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la suppression
        pass

# Attendance
class AttendanceCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        # TODO: Afficher le formulaire d'ajout de présence
        pass
    def post(self, request, student_id, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class AttendanceUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher le formulaire de modification
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class AttendanceDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher la confirmation de suppression
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la suppression
        pass

# Sanction
class SanctionCreateHtmxView(LoginRequiredMixin, View):
    def get(self, request, student_id, *args, **kwargs):
        # TODO: Afficher le formulaire d'ajout de sanction
        pass
    def post(self, request, student_id, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class SanctionUpdateHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher le formulaire de modification
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la soumission
        pass
class SanctionDeleteHtmxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # TODO: Afficher la confirmation de suppression
        pass
    def post(self, request, pk, *args, **kwargs):
        # TODO: Traiter la suppression
        pass
