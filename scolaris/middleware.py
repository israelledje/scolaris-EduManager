import time
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class LastVisitedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Enregistrer le timestamp de la dernière visite
        if hasattr(request, 'user') and request.user.is_authenticated:
            current_time = time.time()
            last_visit = request.session.get('last_visit', current_time)
            
            # Vérifier si plus de 5 minutes se sont écoulées
            if current_time - last_visit > 300:  # 300 secondes = 5 minutes
                # Déconnecter l'utilisateur
                logout(request)
                messages.warning(request, 'Votre session a expiré après 5 minutes d\'inactivité. Veuillez vous reconnecter.')
                return redirect('login')
            
            # Mettre à jour le timestamp de la dernière visite
            request.session['last_visit'] = current_time
        
        response = self.get_response(request)
        return response

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            current_time = time.time()
            last_activity = request.session.get('last_activity', current_time)
            
            # Vérifier l'inactivité (5 minutes)
            if current_time - last_activity > 300:
                logout(request)
                messages.warning(request, 'Session expirée pour inactivité. Veuillez vous reconnecter.')
                return redirect('login')
            
            # Mettre à jour l'activité
            request.session['last_activity'] = current_time
        
        response = self.get_response(request)
        return response 