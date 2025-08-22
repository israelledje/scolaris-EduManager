"""
Système de permissions et de filtres pour l'accès basé sur les rôles
"""
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from school.models import SchoolYear


class TeacherPermissionManager:
    """
    Gestionnaire des permissions pour les professeurs
    """
    
    def __init__(self, user):
        self.user = user
        self.is_teacher = user.role == 'PROFESSEUR'
        self.teacher_profile = getattr(user, 'teacher_profile', None) if hasattr(user, 'teacher_profile') else None
        self.current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
    
    def get_accessible_classes(self):
        """
        Retourne les classes accessibles au professeur
        """
        if not self.is_teacher or not self.teacher_profile:
            return []
        
        if not self.current_year:
            return []
        
        # Classes où le professeur enseigne
        assignments = self.teacher_profile.assignments.filter(year=self.current_year)
        class_ids = list(assignments.values_list('school_class_id', flat=True).distinct())
        
        return class_ids
    
    def get_accessible_students(self):
        """
        Retourne une queryset des étudiants accessibles au professeur
        """
        if not self.is_teacher or not self.teacher_profile:
            return []
        
        accessible_classes = self.get_accessible_classes()
        if not accessible_classes:
            return []
        
        return accessible_classes
    
    def get_accessible_subjects(self):
        """
        Retourne les matières que le professeur peut enseigner
        """
        if not self.is_teacher or not self.teacher_profile:
            return []
        
        if not self.current_year:
            return []
        
        assignments = self.teacher_profile.assignments.filter(year=self.current_year)
        subject_ids = list(assignments.values_list('subject_id', flat=True).distinct())
        
        return subject_ids
    
    def can_access_class(self, class_id):
        """
        Vérifie si le professeur peut accéder à une classe spécifique
        """
        if not self.is_teacher:
            return True  # Les non-professeurs passent par d'autres contrôles
        
        accessible_classes = self.get_accessible_classes()
        return class_id in accessible_classes
    
    def can_access_student(self, student):
        """
        Vérifie si le professeur peut accéder à un étudiant spécifique
        """
        if not self.is_teacher:
            return True
        
        if hasattr(student, 'current_class_id'):
            class_id = student.current_class_id
        elif hasattr(student, 'current_class'):
            class_id = student.current_class.id if student.current_class else None
        else:
            return False
        
        return self.can_access_class(class_id) if class_id else False
    
    def can_access_subject(self, subject_id):
        """
        Vérifie si le professeur peut accéder à une matière spécifique
        """
        if not self.is_teacher:
            return True
        
        accessible_subjects = self.get_accessible_subjects()
        return subject_id in accessible_subjects
    
    def filter_queryset_classes(self, queryset):
        """
        Filtre un queryset de classes selon les permissions du professeur
        """
        if not self.is_teacher or not self.teacher_profile:
            return queryset
        
        accessible_classes = self.get_accessible_classes()
        if not accessible_classes:
            return queryset.none()  # Aucune classe accessible
        
        return queryset.filter(id__in=accessible_classes)
    
    def filter_queryset_students(self, queryset):
        """
        Filtre un queryset d'étudiants selon les permissions du professeur
        """
        if not self.is_teacher or not self.teacher_profile:
            return queryset
        
        accessible_classes = self.get_accessible_classes()
        if not accessible_classes:
            return queryset.none()  # Aucun étudiant accessible
        
        return queryset.filter(current_class_id__in=accessible_classes)
    
    def get_assignment_info(self):
        """
        Retourne les informations sur les assignations du professeur
        """
        if not self.is_teacher or not self.teacher_profile or not self.current_year:
            return {
                'has_assignments': False,
                'classes_count': 0,
                'subjects_count': 0,
                'total_students': 0
            }
        
        assignments = self.teacher_profile.assignments.filter(year=self.current_year)
        
        accessible_classes = self.get_accessible_classes()
        accessible_subjects = self.get_accessible_subjects()
        
        # Compter les étudiants dans les classes accessibles
        if accessible_classes:
            from students.models import Student
            total_students = Student.objects.filter(
                current_class_id__in=accessible_classes,
                is_active=True
            ).count()
        else:
            total_students = 0
        
        return {
            'has_assignments': assignments.exists(),
            'classes_count': len(accessible_classes),
            'subjects_count': len(accessible_subjects),
            'total_students': total_students,
            'assignments': assignments
        }


def check_teacher_permissions(user, resource_type, resource_id=None):
    """
    Fonction utilitaire pour vérifier les permissions d'un professeur
    """
    if user.role != 'PROFESSEUR':
        return True  # Les non-professeurs passent par d'autres contrôles
    
    manager = TeacherPermissionManager(user)
    
    if resource_type == 'class':
        if resource_id:
            return manager.can_access_class(resource_id)
        return manager.get_accessible_classes()
    
    elif resource_type == 'subject':
        if resource_id:
            return manager.can_access_subject(resource_id)
        return manager.get_accessible_subjects()
    
    elif resource_type == 'student':
        if resource_id:
            from students.models import Student
            try:
                student = Student.objects.get(id=resource_id)
                return manager.can_access_student(student)
            except Student.DoesNotExist:
                return False
        return manager.get_accessible_students()
    
    return False


def require_teacher_assignment(user):
    """
    Décorateur/fonction pour s'assurer qu'un professeur a des assignations
    """
    if user.role != 'PROFESSEUR':
        return True
    
    manager = TeacherPermissionManager(user)
    assignment_info = manager.get_assignment_info()
    
    if not assignment_info['has_assignments']:
        raise PermissionDenied(
            "Vous n'avez pas encore été assigné à des classes. "
            "Contactez l'administration pour obtenir vos assignations."
        )
    
    return True
