from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.check_permissions, name='check_permissions'),
    path('user-permissions/', api_views.get_user_permissions, name='user_permissions'),
]
