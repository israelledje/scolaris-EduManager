from django.urls import path
from . import views

app_name = 'parents_portal'

urlpatterns = [
    # ==================== AUTHENTIFICATION ====================
    path('login/', views.parent_login, name='login'),
    path('logout/', views.parent_logout, name='logout'),
    path('register/', views.parent_register, name='register'),
    
    # ==================== TABLEAU DE BORD ====================
    path('', views.parent_dashboard, name='dashboard'),
    
    # ==================== ÉTUDIANTS ====================
    path('students/', views.student_list, name='student_list'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('students/<int:student_id>/grades/', views.get_student_grades, name='student_grades'),
    
    # ==================== BULLETINS ====================
    path('bulletins/<int:bulletin_id>/', views.bulletin_view, name='bulletin_view'),
    
    # ==================== FINANCES ====================
    path('finances/', views.financial_overview, name='financial_overview'),
    path('finances/student/<int:student_id>/', views.student_financial_detail, name='student_financial_detail'),
    
    # Paiements des tranches
    path('finances/payment/tranche/<int:student_id>/<int:tranche_id>/', views.make_tranche_payment, name='make_tranche_payment'),
    
    # Paiements des frais d'inscription
    path('finances/payment/inscription/<int:student_id>/', views.make_inscription_payment, name='make_inscription_payment'),
    
    # Paiements des frais annexes
    path('finances/payment/extra-fee/<int:student_id>/<int:extra_fee_id>/', views.make_extra_fee_payment, name='make_extra_fee_payment'),
    
    # Succès et reçus de paiement
    path('finances/payment/success/<int:payment_id>/', views.payment_success, name='payment_success'),
    path('finances/payment/receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
    
    # Historique et rapports
    path('finances/history/', views.payment_history, name='payment_history'),
    path('finances/reports/', views.financial_reports, name='financial_reports'),
    
    # ==================== PROFIL ====================
    path('profile/', views.parent_profile, name='profile'),
    path('profile/payment-method/add/', views.add_payment_method, name='add_payment_method'),
    path('profile/payment-method/<int:method_id>/remove/', views.remove_payment_method, name='remove_payment_method'),
    
    # ==================== NOTIFICATIONS ====================
    path('notifications/', views.notifications, name='notifications'),
    
    # ==================== API & WEBHOOKS ====================
    path('api/payment-webhook/', views.payment_webhook, name='payment_webhook'),
]
