from django.urls import path
from . import views

app_name = 'subjects'

urlpatterns = [
    # URLs existantes pour les matières
    path('', views.subject_list, name='subject_list'),
    path('create-ajax/', views.subject_create_ajax, name='subject_create_ajax'),
    path('<int:pk>/update-ajax/', views.subject_update_ajax, name='subject_update_ajax'),
    path('<int:pk>/delete-ajax/', views.subject_delete_ajax, name='subject_delete_ajax'),
    path('<int:pk>/detail-ajax/', views.subject_detail_ajax, name='subject_detail_ajax'),
    path('<int:pk>/', views.subject_detail, name='subject_detail'),
    path('create/', views.subject_create_htmx, name='subject_create_htmx'),
    
    # URLs pédagogiques - Tableau de bord et gestion
    path('pedagogy/', views.pedagogy_dashboard, name='pedagogy_dashboard'),
    path('pedagogy/programs/', views.program_list, name='program_list'),
    path('pedagogy/programs/create/', views.program_create, name='program_create'),
    path('pedagogy/programs/<int:pk>/', views.program_detail, name='program_detail'),
    path('pedagogy/units/<int:pk>/', views.unit_detail, name='unit_detail'),
    path('pedagogy/lessons/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('pedagogy/lessons/<int:pk>/change-status/', views.lesson_change_status, name='lesson_change_status'),
    
    # URLs d'intégration avec les classes et élèves
    path('pedagogy/class/<int:class_id>/', views.class_pedagogy_overview, name='class_pedagogy_overview'),
    path('pedagogy/class/<int:class_id>/generate-timetable/', views.generate_timetable_from_programs, name='generate_timetable_from_programs'),
    path('pedagogy/student/<int:student_id>/', views.student_pedagogy_progress, name='student_pedagogy_progress'),

    # Gestion de l'emploi du temps
    path('pedagogy/class/<int:class_id>/timetable/', views.timetable_management, name='timetable_management'),
    path('pedagogy/class/<int:class_id>/create-timetable-slots/', views.create_timetable_slots, name='create_timetable_slots'),
    path('pedagogy/timetable/slot/<int:slot_id>/edit/', views.timetable_slot_edit, name='timetable_slot_edit'),
    path('pedagogy/timetable/slot/<int:slot_id>/delete/', views.timetable_slot_delete, name='timetable_slot_delete'),
] 