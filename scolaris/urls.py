"""
URL configuration for scolaris project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from authentication.views import login_view
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

def root_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    next_url = request.session.get('last_visited')
    if next_url:
        return redirect(next_url)
    return redirect('notes:dashboard')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', login_view, name='login'),
    path('school/', include('school.urls')),
    path('dashboard/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('classes/', include(('classes.urls', 'classes'), namespace='classes')),
    path('students/', include(('students.urls', 'students'), namespace='students')),
    path('teachers/', include(('teachers.urls', 'teachers'), namespace='teachers')),
    path('subjects/', include(('subjects.urls', 'subjects'), namespace='subjects')),
    path('notes/', include(('notes.urls', 'notes'), namespace='notes')),
    path('finances/', include(('finances.urls', 'finances'), namespace='finances')),
    path('documents/', include(('documents.urls', 'documents'), namespace='documents')),
    path('', root_redirect, name='root'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()