from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ParentUser, ParentStudentRelation, ParentPaymentMethod,
    ParentPayment, ParentNotification, ParentLoginSession
)

@admin.register(ParentUser)
class ParentUserAdmin(admin.ModelAdmin):
    """Administration des utilisateurs parents"""
    list_display = [
        'username', 'email', 'get_full_name', 'role', 'status', 
        'is_active', 'date_joined', 'last_login'
    ]
    list_filter = ['role', 'status', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    readonly_fields = ['date_joined', 'created_at', 'updated_at']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'phone')
        }),
        ('Rôle et statut', {
            'fields': ('role', 'status', 'is_active')
        }),
        ('Authentification', {
            'fields': ('password_hash', 'last_login'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Nom complet'
    
    def has_add_permission(self, request):
        """Les comptes parents sont créés automatiquement"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression des comptes parents"""
        return False

@admin.register(ParentStudentRelation)
class ParentStudentRelationAdmin(admin.ModelAdmin):
    """Administration des relations parent-étudiant"""
    list_display = [
        'parent_user', 'student', 'relation_type', 'is_active',
        'can_view_academic', 'can_view_financial', 'can_make_payments'
    ]
    list_filter = [
        'relation_type', 'is_active', 'can_view_academic', 
        'can_view_financial', 'can_make_payments'
    ]
    search_fields = [
        'parent_user__username', 'parent_user__email', 
        'student__first_name', 'student__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Relation', {
            'fields': ('parent_user', 'student', 'relation_type')
        }),
        ('Permissions', {
            'fields': (
                'can_view_academic', 'can_view_financial', 
                'can_make_payments', 'is_active'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ParentPaymentMethod)
class ParentPaymentMethodAdmin(admin.ModelAdmin):
    """Administration des méthodes de paiement"""
    list_display = [
        'parent_user', 'method_type', 'account_name', 
        'account_number', 'is_default', 'is_active'
    ]
    list_filter = ['method_type', 'is_default', 'is_active']
    search_fields = [
        'parent_user__username', 'parent_user__email', 
        'account_name', 'account_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Méthode de paiement', {
            'fields': ('parent_user', 'method_type', 'account_name', 'account_number')
        }),
        ('Configuration', {
            'fields': ('is_default', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Gérer la méthode par défaut"""
        if obj.is_default:
            # Désactiver les autres méthodes par défaut pour ce parent
            ParentPaymentMethod.objects.filter(
                parent_user=obj.parent_user,
                is_default=True
            ).exclude(id=obj.id).update(is_default=False)
        super().save_model(request, obj, form, change)

@admin.register(ParentPayment)
class ParentPaymentAdmin(admin.ModelAdmin):
    """Administration des paiements parents"""
    list_display = [
        'transaction_id', 'parent_user', 'student', 'amount', 
        'status', 'payment_method', 'created_at'
    ]
    list_filter = ['status', 'payment_method__method_type', 'created_at']
    search_fields = [
        'transaction_id', 'parent_user__username', 'parent_user__email',
        'student__first_name', 'student__last_name'
    ]
    readonly_fields = [
        'transaction_id', 'created_at', 'updated_at', 'completed_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations de paiement', {
            'fields': ('transaction_id', 'parent_user', 'student', 'tranche')
        }),
        ('Détails', {
            'fields': ('amount', 'payment_method', 'status')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Les paiements sont créés via le portail"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Empêcher la suppression des paiements"""
        return False

@admin.register(ParentNotification)
class ParentNotificationAdmin(admin.ModelAdmin):
    """Administration des notifications parents"""
    list_display = [
        'parent_user', 'title', 'notification_type', 'is_read', 
        'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = [
        'parent_user__username', 'parent_user__email', 
        'title', 'message'
    ]
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification', {
            'fields': ('parent_user', 'title', 'message', 'notification_type')
        }),
        ('Statut', {
            'fields': ('is_read', 'related_student', 'related_url')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Les notifications sont créées automatiquement"""
        return False

@admin.register(ParentLoginSession)
class ParentLoginSessionAdmin(admin.ModelAdmin):
    """Administration des sessions de connexion"""
    list_display = [
        'parent_user', 'ip_address', 'login_time', 'logout_time', 
        'is_active'
    ]
    list_filter = ['is_active', 'login_time', 'logout_time']
    search_fields = [
        'parent_user__username', 'parent_user__email', 'ip_address'
    ]
    readonly_fields = [
        'parent_user', 'ip_address', 'user_agent', 'login_time', 
        'logout_time', 'created_at'
    ]
    ordering = ['-login_time']
    
    fieldsets = (
        ('Session', {
            'fields': ('parent_user', 'ip_address', 'user_agent')
        }),
        ('Horodatage', {
            'fields': ('login_time', 'logout_time', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Les sessions sont créées automatiquement"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permettre la suppression des anciennes sessions"""
        return True
