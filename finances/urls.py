from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    # ==================== DASHBOARD ET RAPPORTS ====================
    path('', views.financial_dashboard, name='financial_dashboard'),
    path('export-report/', views.export_financial_report, name='export_financial_report'),
    path('student/<int:student_pk>/status/', views.student_financial_status, name='student_financial_status'),
    
    # ==================== STRUCTURES DE FRAIS ====================
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structures/create/', views.fee_structure_create, name='fee_structure_create'),
    path('fee-structures/<int:pk>/', views.fee_structure_detail, name='fee_structure_detail'),
    path('fee-structures/<int:pk>/update/', views.fee_structure_update, name='fee_structure_update'),
    path('fee-structures/<int:pk>/delete/', views.fee_structure_delete, name='fee_structure_delete'),
    
    # ==================== TRANCHES ====================
    path('fee-structures/<int:fee_structure_pk>/tranches/create/', views.fee_tranche_create, name='fee_tranche_create'),
    path('tranches/<int:pk>/update/', views.fee_tranche_update, name='fee_tranche_update'),
    path('tranches/<int:pk>/delete/', views.fee_tranche_delete, name='fee_tranche_delete'),
    
    # ==================== PAIEMENTS ====================
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/inscription/create/', views.inscription_payment_create, name='inscription_payment_create'),
    path('payments/bulk/', views.bulk_payment_create, name='bulk_payment_create'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/receipt/', views.payment_receipt, name='payment_receipt'),
    path('payments/<int:pk>/receipt/pdf/', views.payment_receipt_pdf, name='payment_receipt_pdf'),
    # Routes typées pour désambiguïser le type de paiement
    path('payments/<str:payment_type>/<int:pk>/', views.payment_detail, name='payment_detail_typed'),
    path('payments/<str:payment_type>/<int:pk>/receipt/', views.payment_receipt, name='payment_receipt_typed'),
    path('payments/<str:payment_type>/<int:pk>/receipt/pdf/', views.payment_receipt_pdf, name='payment_receipt_pdf_typed'),
    
    # ==================== REMISES/BOURSES ====================
    path('discounts/', views.discount_list, name='discount_list'),
    path('discounts/create/', views.discount_create, name='discount_create'),
    path('discounts/<int:pk>/update/', views.discount_update, name='discount_update'),
    path('discounts/<int:pk>/delete/', views.discount_delete, name='discount_delete'),
    
    # ==================== MORATOIRES ====================
    path('moratoriums/', views.moratorium_list, name='moratorium_list'),
    path('moratoriums/create/', views.moratorium_create, name='moratorium_create'),
    path('moratoriums/<int:pk>/approve/', views.moratorium_approve, name='moratorium_approve'),
    path('moratoriums/<int:pk>/approved/', views.moratorium_approved, name='moratorium_approved'),
    path('moratoriums/<int:pk>/pdf/', views.moratorium_pdf, name='moratorium_pdf'),
    path('moratoriums/<int:pk>/delete/', views.moratorium_delete, name='moratorium_delete'),
    
    # ==================== REMBOURSEMENTS ====================
    path('refunds/', views.refund_list, name='refund_list'),
    path('refunds/create/', views.refund_create, name='refund_create'),
    
    # ==================== FRAIS ANNEXES ====================
    path('extra-fees/', views.extra_fee_list, name='extra_fee_list'),
    path('extra-fees/create/', views.extra_fee_create, name='extra_fee_create'),
    path('extra-fees/<int:pk>/', views.extra_fee_detail, name='extra_fee_detail'),
    path('extra-fees/<int:pk>/update/', views.extra_fee_update, name='extra_fee_update'),
    path('extra-fees/<int:pk>/delete/', views.extra_fee_delete, name='extra_fee_delete'),
    
    # ==================== TYPES DE FRAIS ANNEXES ====================
    path('extra-fee-types/', views.extra_fee_type_list, name='extra_fee_type_list'),
    path('extra-fee-types/create/', views.extra_fee_type_create, name='extra_fee_type_create'),
    path('extra-fee-types/<int:pk>/update/', views.extra_fee_type_update, name='extra_fee_type_update'),
    path('extra-fee-types/<int:pk>/delete/', views.extra_fee_type_delete, name='extra_fee_type_delete'),
    
    # ==================== PAIEMENTS FRAIS ANNEXES ====================
    path('extra-fee-payments/', views.extra_fee_payment_list, name='extra_fee_payment_list'),
    path('extra-fee-payments/create/', views.extra_fee_payment_create, name='extra_fee_payment_create'),
    path('extra-fee-payments/<int:pk>/', views.extra_fee_payment_detail, name='extra_fee_payment_detail'),
    path('extra-fee-payments/<int:pk>/receipt/pdf/', views.extra_fee_payment_receipt_pdf, name='extra_fee_payment_receipt_pdf'),
    
    # ==================== VUES AJAX ====================
    path('ajax/tranches-for-class/', views.get_tranches_for_class, name='get_tranches_for_class'),
    path('ajax/tranches-for-student/', views.get_tranches_for_class, name='get_tranches_for_student'),
    path('ajax/search-students/', views.search_students, name='search_students'),
    path('ajax/get-student-info/', views.get_student_info, name='get_student_info'),
    path('ajax/get-classes-with-fee-structures/', views.get_classes_with_fee_structures, name='get_classes_with_fee_structures'),
    path('ajax/get-students-for-class/', views.get_students_for_class, name='get_students_for_class'),
    
    # ==================== API FRAIS ANNEXES ====================
    path('api/classes-for-extra-fee/<int:extra_fee_id>/', views.get_classes_for_extra_fee, name='get_classes_for_extra_fee'),
    path('api/students-for-class/<int:class_id>/', views.get_students_for_class_api, name='get_students_for_class_api'),
    path('api/amount-for-extra-fee/<int:extra_fee_id>/<int:class_id>/<int:student_id>/', views.get_amount_for_extra_fee, name='get_amount_for_extra_fee'),
    path('api/extra-fee-amount/<int:extra_fee_id>/', views.extra_fee_amount, name='extra_fee_amount'),
    path('api/search-students/', views.search_students_api, name='search_students_api'),
    
    # ==================== RAPPORTS SPÉCIALISÉS ====================
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    
    # Rapports d'inscription
    path('reports/inscriptions/', views.inscriptions_report, name='inscriptions_report'),
    path('reports/inscriptions/class/<int:class_id>/', views.inscriptions_report_class, name='inscriptions_report_class'),
    path('reports/inscriptions/export-pdf/', views.export_inscriptions_report, name='export_inscriptions_report'),
    
    # Rapports de scolarité
    path('reports/tuition/', views.tuition_report, name='tuition_report'),
    path('reports/tuition/class/<int:class_id>/', views.tuition_report_class, name='tuition_report_class'),
    path('reports/tuition/export-pdf/', views.export_tuition_report, name='export_tuition_report'),
    
    # Rapports de retards
    path('reports/overdue/', views.overdue_report, name='overdue_report'),
    path('reports/overdue/class/<int:class_id>/', views.overdue_report_class, name='overdue_report_class'),
    path('reports/overdue/export-pdf/', views.export_overdue_report, name='export_overdue_report'),
    
    # Rapports de performance
    path('reports/performance/', views.performance_report, name='performance_report'),
    path('reports/performance/export-pdf/', views.export_performance_report, name='export_performance_report'),
    
    # Rapports par étudiant
    path('reports/student/<int:student_id>/', views.student_report, name='student_report'),
    path('reports/student/<int:student_id>/export-pdf/', views.export_student_report, name='export_student_report'),
] 