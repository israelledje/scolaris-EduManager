from django.db.models import Q
from school.models import SchoolYear

def user_permissions(request):
    """
    Context processor qui fournit les informations de permissions et rôles de l'utilisateur
    pour l'affichage conditionnel du menu
    """
    context = {
        'user_role': None,
        'teacher_profile': None,
        'teacher_assignments': [],
        'can_view_finances': False,
        'can_view_all_classes': False,
        'can_view_all_students': False,
        'can_view_admin': False,
        'accessible_classes': [],
        'accessible_subjects': [],
    }
    
    if not request.user.is_authenticated:
        return context
        
    user = request.user
    context['user_role'] = user.role
    
    # Permissions selon le rôle
    if user.role in ['ADMIN', 'DIRECTION']:
        context.update({
            'can_view_finances': True,
            'can_view_all_classes': True,
            'can_view_all_students': True,
            'can_view_admin': True,
        })
    
    elif user.role == 'SURVEILLANCE':
        context.update({
            'can_view_all_classes': True,
            'can_view_all_students': True,
        })
    
    elif user.role == 'PROFESSEUR':
        # Utiliser le gestionnaire de permissions pour les professeurs
        try:
            from authentication.permissions import TeacherPermissionManager
            permission_manager = TeacherPermissionManager(user)
            assignment_info = permission_manager.get_assignment_info()
            
            context.update({
                'teacher_profile': permission_manager.teacher_profile,
                'teacher_assignments': assignment_info.get('assignments', []),
                'teacher_has_assignments': assignment_info['has_assignments'],
                'teacher_assignment_info': assignment_info,
                'accessible_classes': permission_manager.get_accessible_classes(),
                'accessible_subjects': permission_manager.get_accessible_subjects(),
            })
            
        except (AttributeError, ImportError):
            # L'utilisateur n'a pas de profil enseignant lié ou erreur d'import
            pass
    
    # Ajouter les compteurs selon les permissions
    try:
        from students.models import Student
        from teachers.models import Teacher  
        from classes.models import SchoolClass
        
        if user.role == 'PROFESSEUR':
            # Pour les professeurs, utiliser les données filtrées
            if context.get('teacher_has_assignments') and context.get('accessible_classes'):
                context['students_count'] = Student.objects.filter(
                    current_class_id__in=context['accessible_classes'],
                    is_active=True
                ).count()
                context['classes_count'] = len(context['accessible_classes'])
            else:
                # Professeur sans assignation : compteurs à zéro
                context['students_count'] = 0
                context['classes_count'] = 0
                
            # Le professeur ne voit que lui-même dans la liste des enseignants
            context['teachers_count'] = 1
        else:
            # Compteurs globaux pour les autres rôles
            context['students_count'] = Student.objects.filter(is_active=True).count()
            context['classes_count'] = SchoolClass.objects.filter(is_active=True).count()
            context['teachers_count'] = Teacher.objects.filter(is_active=True).count()
        
    except ImportError:
        # En cas d'erreur d'import, valeurs par défaut
        context.update({
            'students_count': 0,
            'teachers_count': 0,
            'classes_count': 0,
        })
    
    return context
