from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    # Paramètres des matricules
    path('matricule/', views.matricule_settings, name='matricule_settings'),
    path('matricule/update/<int:sequence_id>/', views.update_matricule_sequence, name='update_matricule_sequence'),
    path('matricule/reset/<int:sequence_id>/', views.reset_sequence, name='reset_sequence'),
    path('matricule/test/<int:sequence_id>/', views.generate_test_matricule, name='generate_test_matricule'),
    path('matricule/info/<str:sequence_type>/', views.get_sequence_info, name='get_sequence_info'),
    
    # Gestion des comptes utilisateurs
    path('user-accounts/', views.user_accounts_management, name='user_accounts_management'),
    path('user-accounts/create/', views.create_teacher_accounts_bulk, name='create_teacher_accounts_bulk'),
    path('user-accounts/reset-password/<int:teacher_id>/', views.reset_teacher_password, name='reset_teacher_password'),
]
