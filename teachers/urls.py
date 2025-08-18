from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('create/', views.teacher_create_htmx, name='teacher_create_htmx'),
    path('<int:pk>/update/', views.teacher_update_htmx, name='teacher_update_htmx'),
    path('<int:pk>/delete/', views.teacher_delete_htmx, name='teacher_delete_htmx'),
    path('<int:pk>/assign-subjects/', views.teacher_assign_subjects_htmx, name='teacher_assign_subjects_htmx'),
    path('<int:pk>/assign-classes/', views.teacher_assign_classes_htmx, name='teacher_assign_classes_htmx'),
    path('assignment/create/<int:class_id>/', views.teaching_assignment_create_htmx, name='teaching_assignment_create_htmx'),
    path('assignment/<int:pk>/update/', views.teaching_assignment_update_htmx, name='teaching_assignment_update_htmx'),
    path('assignment/<int:pk>/delete/', views.teaching_assignment_delete_htmx, name='teaching_assignment_delete_htmx'),
    path('assignment/teacher-select/', views.teacher_select_for_subject_htmx, name='teacher_select_for_subject_htmx'),
    path('assignment/<int:pk>/titulaire/', views.teaching_assignment_update_titulaire_htmx, name='teaching_assignment_update_titulaire_htmx'),
    path('assignment/<int:pk>/coef-update/', views.teaching_assignment_coef_update_htmx, name='teaching_assignment_coef_update_htmx'),
    path('assignment/<int:pk>/full-update/', views.teaching_assignment_full_update_htmx, name='teaching_assignment_full_update_htmx'),
    path('assignment/bulk-delete/', views.teaching_assignment_bulk_delete_htmx, name='teaching_assignment_bulk_delete_htmx'),
]