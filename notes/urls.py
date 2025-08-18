from django.urls import path
from . import views

app_name = 'notes'

urlpatterns = [
    # ==================== DASHBOARD ====================
    path('', views.notes_dashboard, name='dashboard'),
    
    # ==================== GESTION DES TRIMESTRES ====================
    path('trimesters/', views.trimester_list, name='trimester_list'),
    path('trimesters/create/', views.trimester_create, name='trimester_create'),
    path('trimesters/<int:pk>/', views.trimester_detail, name='trimester_detail'),
    path('trimesters/<int:pk>/update/', views.trimester_update, name='trimester_update'),
    path('trimesters/<int:pk>/delete/', views.trimester_delete, name='trimester_delete'),
    
    # ==================== GESTION DES ÉVALUATIONS ====================
    path('evaluations/', views.evaluation_list, name='evaluation_list'),
    path('evaluations/class/<int:class_id>/', views.class_evaluations_list, name='class_evaluations_list'),
    path('evaluations/create/', views.evaluation_create, name='evaluation_create'),
    path('evaluations/<int:pk>/', views.evaluation_detail, name='evaluation_detail'),
    path('evaluations/<int:pk>/update/', views.evaluation_update, name='evaluation_update'),
    path('evaluations/<int:pk>/delete/', views.evaluation_delete, name='evaluation_delete'),
    path('evaluations/<int:pk>/close/', views.evaluation_close, name='evaluation_close'),
    
    # ==================== SAISIE DES NOTES ====================
    path('grades/', views.grade_list, name='grade_list'),
    path('grades/evaluation/<int:evaluation_id>/', views.grade_entry, name='grade_entry'),
    path('grades/bulk/<int:evaluation_id>/', views.bulk_grade_entry, name='bulk_grade_entry'),
    path('grades/<int:pk>/update/', views.grade_update, name='grade_update'),
    path('grades/<int:pk>/delete/', views.grade_delete, name='grade_delete'),
    
    # ==================== GESTION DES BULLETINS ====================
    path('bulletins/', views.bulletin_list, name='bulletin_list'),
    path('bulletins/generate/<int:trimester_id>/', views.generate_bulletins, name='generate_bulletins'),
    path('bulletins/pdf-batch/', views.bulletin_pdf_batch, name='bulletin_pdf_batch'),
    path('bulletins/<int:pk>/', views.bulletin_detail, name='bulletin_detail'),
    path('bulletins/<int:pk>/pdf/', views.bulletin_pdf, name='bulletin_pdf'),
    path('bulletins/<int:pk>/approve/', views.bulletin_approve, name='bulletin_approve'),
    
    # ==================== AJAX ENDPOINTS ====================
    path('ajax/classes-for-trimester/<int:trimester_id>/', views.get_classes_for_trimester, name='get_classes_for_trimester'),
    path('ajax/subjects-for-class/<int:class_id>/', views.get_subjects_for_class, name='get_subjects_for_class'),
    path('ajax/students-for-evaluation/<int:evaluation_id>/', views.get_students_for_evaluation, name='get_students_for_evaluation'),
    path('ajax/save-grade/', views.save_grade_ajax, name='save_grade_ajax'),
    path('ajax/evaluation-stats/<int:evaluation_id>/', views.get_evaluation_stats, name='get_evaluation_stats'),
    
    # ==================== RAPPORTS ET STATISTIQUES ====================
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/class-performance/<int:class_id>/', views.class_performance_report, name='class_performance_report'),
    path('reports/student-progress/<int:student_id>/', views.student_progress_report, name='student_progress_report'),
    path('reports/subject-analysis/<int:subject_id>/', views.subject_analysis_report, name='subject_analysis_report'),
    
    # ==================== IMPORT/EXPORT ====================
    path('import-export/', views.import_export_dashboard, name='import_export_dashboard'),
    path('export/grades/<int:evaluation_id>/', views.export_grades, name='export_grades'),
    path('import/grades/<int:evaluation_id>/', views.import_grades, name='import_grades'),
]
