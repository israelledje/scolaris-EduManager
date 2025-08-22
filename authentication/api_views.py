from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.urls import reverse, resolve, Resolver404
import json

@login_required
@require_http_methods(["POST"])
def check_permissions(request):
    """
    API endpoint pour vérifier les permissions d'accès à une URL
    """
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
        
        if not url:
            return JsonResponse({
                'error': True,
                'message': 'URL requise'
            }, status=400)
        
        # Nettoyer l'URL
        if url.startswith('/'):
            url = url[1:]
        
        try:
            # Résoudre l'URL pour obtenir la vue
            resolved = resolve('/' + url)
            view_func = resolved.func
            
            # Extraire les informations sur les permissions requises
            permissions_info = _extract_permission_info(view_func, resolved.url_name)
            
            # Vérifier si l'utilisateur a les permissions
            has_permission = _check_user_permission(request.user, permissions_info)
            
            return JsonResponse({
                'has_permission': has_permission,
                'user_role': request.user.role if request.user.is_authenticated else None,
                'required_roles': permissions_info.get('required_roles', []),
                'permission_type': permissions_info.get('type', 'unknown'),
                'url': url
            })
            
        except Resolver404:
            return JsonResponse({
                'error': True,
                'message': 'URL non trouvée'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': True,
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': True,
            'message': f'Erreur interne: {str(e)}'
        }, status=500)

def _extract_permission_info(view_func, url_name):
    """
    Extrait les informations de permissions d'une vue
    """
    info = {
        'type': 'unknown',
        'required_roles': [],
        'description': ''
    }
    
    # Vérifier les décorateurs et mixins
    if hasattr(view_func, 'view_class'):
        # Vue basée sur une classe
        view_class = view_func.view_class
        
        # Vérifier les mixins de permission
        from authentication.mixins import (
            AdminOrDirectionRequiredMixin, 
            RoleRequiredMixin, 
            TeacherAccessMixin
        )
        
        if issubclass(view_class, AdminOrDirectionRequiredMixin):
            info.update({
                'type': 'admin_or_direction',
                'required_roles': ['ADMIN', 'DIRECTION'],
                'description': 'Accès réservé aux administrateurs et à la direction'
            })
        elif issubclass(view_class, RoleRequiredMixin):
            if hasattr(view_class, 'allowed_roles'):
                info.update({
                    'type': 'role_required',
                    'required_roles': view_class.allowed_roles,
                    'description': f'Rôles requis: {", ".join(view_class.allowed_roles)}'
                })
        elif issubclass(view_class, TeacherAccessMixin):
            info.update({
                'type': 'teacher_access',
                'required_roles': ['ADMIN', 'DIRECTION', 'SURVEILLANCE', 'PROFESSEUR'],
                'description': 'Accès pour le personnel enseignant avec restrictions'
            })
    
    # Analyser l'URL pour déduire les permissions
    if url_name:
        if 'settings' in url_name or 'admin' in url_name:
            info.update({
                'type': 'admin_required',
                'required_roles': ['ADMIN', 'DIRECTION'],
                'description': 'Zone d\'administration'
            })
        elif 'finance' in url_name:
            info.update({
                'type': 'finance_access',
                'required_roles': ['ADMIN', 'DIRECTION'],
                'description': 'Accès aux finances'
            })
        elif 'teacher' in url_name:
            info.update({
                'type': 'teacher_management',
                'required_roles': ['ADMIN', 'DIRECTION', 'SURVEILLANCE'],
                'description': 'Gestion des enseignants'
            })
    
    return info

def _check_user_permission(user, permissions_info):
    """
    Vérifie si un utilisateur a les permissions requises
    """
    if not user.is_authenticated:
        return False
    
    required_roles = permissions_info.get('required_roles', [])
    
    if not required_roles:
        return True  # Pas de restriction
    
    return user.role in required_roles

@login_required
def get_user_permissions(request):
    """
    Retourne les permissions de l'utilisateur actuel
    """
    user = request.user
    
    # Déterminer les permissions selon le rôle
    permissions = {
        'role': user.role,
        'can_access_admin': user.role in ['ADMIN', 'DIRECTION'],
        'can_access_finances': user.role in ['ADMIN', 'DIRECTION'],
        'can_manage_teachers': user.role in ['ADMIN', 'DIRECTION', 'SURVEILLANCE'],
        'can_manage_students': user.role in ['ADMIN', 'DIRECTION', 'SURVEILLANCE', 'PROFESSEUR'],
        'can_access_all_classes': user.role in ['ADMIN', 'DIRECTION', 'SURVEILLANCE'],
        'can_access_settings': user.role in ['ADMIN', 'DIRECTION'],
    }
    
    # Pour les professeurs, ajouter les classes/matières accessibles
    if user.role == 'PROFESSEUR':
        try:
            teacher_profile = user.teacher_profile
            if teacher_profile:
                from school.models import SchoolYear
                current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
                
                if current_year:
                    assignments = teacher_profile.assignments.filter(year=current_year)
                    permissions.update({
                        'accessible_classes': list(assignments.values_list('school_class_id', flat=True)),
                        'accessible_subjects': list(assignments.values_list('subject_id', flat=True)),
                        'assignment_count': assignments.count()
                    })
        except AttributeError:
            pass
    
    return JsonResponse(permissions)
