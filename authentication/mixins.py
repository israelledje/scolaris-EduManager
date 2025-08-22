from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from school.models import SchoolYear

class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier si l'utilisateur a un rôle spécifique
    """
    allowed_roles = []
    
    def test_func(self):
        return (
            self.request.user.is_authenticated and 
            self.request.user.role in self.allowed_roles
        )
    
    def handle_no_permission(self):
        raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette page.")


class AdminOrDirectionRequiredMixin(RoleRequiredMixin):
    """
    Mixin pour les pages qui nécessitent des droits d'admin ou de direction
    """
    allowed_roles = ['ADMIN', 'DIRECTION']


class TeacherAccessMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'enseignant a accès à une ressource spécifique
    (classe, matière, élève)
    """
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
            
        user = self.request.user
        
        # Admin et Direction ont accès à tout
        if user.role in ['ADMIN', 'DIRECTION', 'SURVEILLANCE']:
            return True
            
        # Pour les professeurs, vérifier les assignations
        if user.role == 'PROFESSEUR':
            return self.check_teacher_access()
            
        return False
    
    def check_teacher_access(self):
        """
        Méthode à surcharger dans les vues spécifiques pour vérifier
        l'accès de l'enseignant à la ressource
        """
        return True
    
    def handle_no_permission(self):
        raise PermissionDenied("Vous n'avez pas accès à cette ressource.")


class ClassAccessMixin(TeacherAccessMixin):
    """
    Mixin pour vérifier l'accès d'un enseignant à une classe spécifique
    """
    
    def check_teacher_access(self):
        try:
            teacher_profile = self.request.user.teacher_profile
            current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
            
            if not teacher_profile or not current_year:
                return False
                
            # Récupérer la classe depuis l'URL (pk)
            class_id = self.kwargs.get('pk') or self.kwargs.get('class_id')
            if not class_id:
                return True  # Si pas de classe spécifique, on autorise
                
            # Vérifier si l'enseignant a des assignations dans cette classe
            return teacher_profile.assignments.filter(
                school_class_id=class_id,
                year=current_year
            ).exists()
            
        except AttributeError:
            return False


class SubjectAccessMixin(TeacherAccessMixin):
    """
    Mixin pour vérifier l'accès d'un enseignant à une matière spécifique
    """
    
    def check_teacher_access(self):
        try:
            teacher_profile = self.request.user.teacher_profile
            current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
            
            if not teacher_profile or not current_year:
                return False
                
            # Récupérer la matière depuis l'URL
            subject_id = self.kwargs.get('subject_id')
            if not subject_id:
                return True  # Si pas de matière spécifique, on autorise
                
            # Vérifier si l'enseignant enseigne cette matière
            return teacher_profile.assignments.filter(
                subject_id=subject_id,
                year=current_year
            ).exists()
            
        except AttributeError:
            return False


class StudentAccessMixin(TeacherAccessMixin):
    """
    Mixin pour vérifier l'accès d'un enseignant à un élève spécifique
    """
    
    def check_teacher_access(self):
        try:
            teacher_profile = self.request.user.teacher_profile
            current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
            
            if not teacher_profile or not current_year:
                return False
                
            # Récupérer l'élève depuis l'URL
            from students.models import Student
            student_id = self.kwargs.get('pk') or self.kwargs.get('student_id')
            if not student_id:
                return True  # Si pas d'élève spécifique, on autorise
                
            try:
                student = Student.objects.get(pk=student_id)
                # Vérifier si l'enseignant a des assignations dans la classe de l'élève
                return teacher_profile.assignments.filter(
                    school_class=student.current_class,
                    year=current_year
                ).exists()
            except Student.DoesNotExist:
                return False
                
        except AttributeError:
            return False


class EvaluationAccessMixin(TeacherAccessMixin):
    """
    Mixin pour vérifier l'accès d'un enseignant à une évaluation
    (il doit enseigner la matière dans la classe concernée)
    """
    
    def check_teacher_access(self):
        try:
            teacher_profile = self.request.user.teacher_profile
            current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
            
            if not teacher_profile or not current_year:
                return False
                
            # Récupérer l'évaluation ou ses paramètres depuis l'URL/contexte
            evaluation_id = self.kwargs.get('pk') or self.kwargs.get('evaluation_id')
            class_id = self.kwargs.get('class_id')
            subject_id = self.kwargs.get('subject_id')
            
            if evaluation_id:
                # Vérification via l'évaluation existante
                try:
                    from notes.models import Evaluation
                    evaluation = Evaluation.objects.get(pk=evaluation_id)
                    return teacher_profile.assignments.filter(
                        school_class=evaluation.school_class,
                        subject=evaluation.subject,
                        year=current_year
                    ).exists()
                except Evaluation.DoesNotExist:
                    return False
            elif class_id and subject_id:
                # Vérification via classe et matière
                return teacher_profile.assignments.filter(
                    school_class_id=class_id,
                    subject_id=subject_id,
                    year=current_year
                ).exists()
            
            return True  # Si pas de contrainte spécifique
                
        except (AttributeError, ImportError):
            return False


def teacher_required(view_func):
    """
    Décorateur pour les vues qui nécessitent d'être un enseignant
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Vous devez être connecté.")
            
        if request.user.role not in ['ADMIN', 'DIRECTION', 'SURVEILLANCE', 'PROFESSEUR']:
            raise PermissionDenied("Accès réservé au personnel enseignant.")
            
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_direction_required(view_func):
    """
    Décorateur pour les vues qui nécessitent des droits d'admin ou de direction
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Vous devez être connecté.")
            
        if request.user.role not in ['ADMIN', 'DIRECTION']:
            raise PermissionDenied("Accès réservé aux administrateurs et à la direction.")
            
        return view_func(request, *args, **kwargs)
    return wrapper
