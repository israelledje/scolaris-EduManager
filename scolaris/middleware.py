from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import json
import datetime


class PermissionDeniedMiddleware:
    """
    Middleware pour gérer les erreurs de permissions de façon élégante
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Traite les exceptions PermissionDenied
        """
        if isinstance(exception, PermissionDenied):
            
            # Si c'est une requête AJAX, retourner JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': True,
                    'permission_denied': True,
                    'message': str(exception) or "Vous n'avez pas les droits nécessaires pour accéder à cette page.",
                    'user_role': getattr(request.user, 'role', None) if request.user.is_authenticated else None,
                    'required_roles': self._extract_required_roles(exception),
                    'redirect_url': '/dashboard/'
                }, status=403)
            
            # Si l'utilisateur n'est pas connecté, rediriger vers login
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            
            # Pour les requêtes normales, afficher une page d'erreur avec modale
            context = {
                'error_message': str(exception) or "Vous n'avez pas les droits nécessaires pour accéder à cette page.",
                'user_role': request.user.role if request.user.is_authenticated else None,
                'required_roles': self._extract_required_roles(exception),
                'show_permission_modal': True,
                'current_url': request.get_full_path(),
            }
            
            # Ajouter un message pour la modale
            messages.error(request, f"Accès refusé : {str(exception)}")
            
            return render(request, 'errors/permission_denied.html', context, status=403)
        
        return None
    
    def _extract_required_roles(self, exception):
        """
        Extrait les rôles requis du message d'exception si possible
        """
        message = str(exception).lower()
        
        if 'admin' in message:
            return ['ADMIN']
        elif 'direction' in message:
            return ['ADMIN', 'DIRECTION']
        elif 'enseignant' in message or 'professeur' in message:
            return ['ADMIN', 'DIRECTION', 'PROFESSEUR']
        elif 'surveillance' in message:
            return ['ADMIN', 'DIRECTION', 'SURVEILLANCE']
        
        return []


class AutoLogoutMiddleware:
    """
    Middleware pour la déconnexion automatique basée sur l'inactivité
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si l'utilisateur est connecté
        if request.user.is_authenticated:
            # Récupérer le timestamp de la dernière activité
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Convertir en datetime si c'est un string
                if isinstance(last_activity, str):
                    try:
                        last_activity = datetime.datetime.fromisoformat(last_activity)
                    except ValueError:
                        last_activity = timezone.now()
                
                # Calculer le temps d'inactivité
                inactive_duration = timezone.now() - last_activity
                max_inactive_time = datetime.timedelta(seconds=getattr(settings, 'SESSION_COOKIE_AGE', 3600))
                
                # Si l'utilisateur est inactif depuis trop longtemps
                if inactive_duration > max_inactive_time:
                    # Déconnecter l'utilisateur
                    logout(request)
                    messages.warning(request, "Votre session a expiré en raison d'une inactivité prolongée.")
                    
                    # Rediriger vers la page de connexion si ce n'est pas déjà une page publique
                    if not self._is_public_url(request.path):
                        return redirect('login')
            
            # Mettre à jour le timestamp de la dernière activité pour les requêtes non-AJAX
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                request.session['last_activity'] = timezone.now().isoformat()
                request.session.modified = True

        response = self.get_response(request)
        return response
    
    def _is_public_url(self, path):
        """
        Vérifie si l'URL est publique (accessible sans authentification)
        """
        public_urls = [
            '/login/',
            '/logout/',
            '/admin/',
            '/static/',
            '/media/',
            '/parents/',  # Portail parents a sa propre authentification
        ]
        
        for public_url in public_urls:
            if path.startswith(public_url):
                return True
        return False


class LastVisitedMiddleware:
    """
    Middleware pour traquer la dernière page visitée par l'utilisateur
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Sauvegarder l'URL actuelle avant de traiter la requête
        current_url = request.get_full_path()
        
        # Exclure certaines URLs du tracking
        excluded_urls = [
            '/static/',
            '/media/',
            '/api/',
            '/logout/',
            '/login/',
        ]
        
        should_track = True
        for excluded in excluded_urls:
            if current_url.startswith(excluded):
                should_track = False
                break
        
        # Traiter la requête
        response = self.get_response(request)
        
        # Sauvegarder l'URL visitée si l'utilisateur est connecté et si on doit la traquer
        if (request.user.is_authenticated and should_track and 
            response.status_code == 200 and 
            request.method == 'GET'):
            
            # Éviter de sauvegarder la même URL de façon répétitive
            last_visited = request.session.get('last_visited_url')
            if last_visited != current_url:
                request.session['last_visited_url'] = current_url
                request.session['last_visited_time'] = timezone.now().isoformat()
                request.session.modified = True
        
        return response


class SecurityHeadersMiddleware:
    """
    Middleware pour ajouter des headers de sécurité
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Ajouter des headers de sécurité
        if not settings.DEBUG:  # Uniquement en production
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
        return response