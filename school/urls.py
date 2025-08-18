from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    path('config-school/', views.config_school_view, name='config_school'),
    path('init-system/', views.init_system_view, name='init_system'),
    path('init-system-data/', views.init_system_data, name='init_system_data'),
]
