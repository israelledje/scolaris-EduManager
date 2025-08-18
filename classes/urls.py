from django.urls import path
from . import views

urlpatterns = [
    # SchoolClass HTMX CRUD
    path('create/htmx/', views.schoolclass_create_htmx, name='schoolclass_create_htmx'),
    path('<int:pk>/update/htmx/', views.schoolclass_update_htmx, name='schoolclass_update_htmx'),
    path('<int:pk>/delete/htmx/', views.schoolclass_delete_htmx, name='schoolclass_delete_htmx'),

    # Timetable HTMX CRUD
    path('timetable/create/htmx/', views.timetable_create_htmx, name='timetable_create_htmx'),
    path('timetable/<int:pk>/update/htmx/', views.timetable_update_htmx, name='timetable_update_htmx'),
    path('timetable/<int:pk>/delete/htmx/', views.timetable_delete_htmx, name='timetable_delete_htmx'),

    # Timetable list
    path('timetables/', views.timetable_list, name='timetable_list'),
    path('timetable/classes/', views.timetable_list_classes, name='timetable_list_classes'),

    # SchoolClass list & detail
    path('classes/', views.schoolclass_list, name='schoolclass_list'),
    path('classes/<int:pk>/', views.schoolclass_detail, name='schoolclass_detail'),

    path('<int:class_id>/export_students/', views.export_students_excel, name='export_students_excel'),
    path('<int:class_id>/print_pdf/', views.schoolclass_print_pdf, name='schoolclass_print_pdf'),

    path('classe/<int:class_id>/emploi-du-temps/', views.timetable_interactive, name='timetable_interactive'),

    path('slot/add/', views.slot_add_htmx, name='slot_add_htmx'),
    path('slot/<int:slot_id>/edit/', views.slot_edit_htmx, name='slot_edit_htmx'),

    path('assign-subjects-bulk/', views.assign_subjects_bulk, name='assign_subjects_bulk'),
    path('<int:class_id>/assign-main-teacher/', views.assign_main_teacher_htmx, name='assign_main_teacher_htmx'),
    
    # Gestion des créneaux d'emploi du temps
    path('timetable-slot/update/', views.update_timetable_slot, name='update_timetable_slot'),
    path('timetable-slot/delete/', views.delete_timetable_slot, name='delete_timetable_slot'),
] 