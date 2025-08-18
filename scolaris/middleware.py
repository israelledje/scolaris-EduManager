from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve

class LastVisitedMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # On ignore les requêtes AJAX, admin, login/logout, static/media
        path = request.path
        if request.user.is_authenticated and not (
            path.startswith('/admin') or
            path.startswith('/static') or
            path.startswith('/media') or
            path.startswith('/login') or
            path.startswith('/logout') or
            path == '/'
        ):
            request.session['last_visited'] = path 