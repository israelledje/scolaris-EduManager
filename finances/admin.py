from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum
from .models import (
    FeeStructure, FeeTranche, TranchePayment, InscriptionPayment, FeeDiscount, 
    Moratorium, PaymentRefund, ExtraFee, ExtraFeeType, ExtraFeePayment
)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['school_class', 'year', 'inscription_fee', 'tuition_total', 'tranche_count', 'get_total_paid', 'get_total_remaining']
    list_filter = ['year', 'school_class__level', 'school_class']
    search_fields = ['school_class__name', 'year__annee']
    readonly_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('school_class', 'year', 'inscription_fee', 'tuition_total', 'tranche_count')
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_paid(self, obj):
        total = TranchePayment.objects.filter(tranche__fee_structure=obj).aggregate(total=Sum('amount'))['total'] or 0
        return f"{total:,.0f} FCFA"
    get_total_paid.short_description = "Total Payé"
    
    def get_total_remaining(self, obj):
        total_paid = TranchePayment.objects.filter(tranche__fee_structure=obj).aggregate(total=Sum('amount'))['total'] or 0
        total_discounts = FeeDiscount.objects.filter(tranche__fee_structure=obj).aggregate(total=Sum('amount'))['total'] or 0
        remaining = obj.tuition_total - total_paid - total_discounts
        return f"{remaining:,.0f} FCFA"
    get_total_remaining.short_description = "Reste à Payer"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle création
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(FeeTranche)
class FeeTrancheAdmin(admin.ModelAdmin):
    list_display = ['fee_structure', 'number', 'amount', 'due_date', 'get_payment_status']
    list_filter = ['fee_structure__year', 'fee_structure__school_class', 'due_date']
    search_fields = ['fee_structure__school_class__name', 'fee_structure__year__annee']
    ordering = ['fee_structure', 'number']
    
    def get_payment_status(self, obj):
        from django.utils import timezone
        total_paid = TranchePayment.objects.filter(tranche=obj).aggregate(total=Sum('amount'))['total'] or 0
        total_discounts = FeeDiscount.objects.filter(tranche=obj).aggregate(total=Sum('amount'))['total'] or 0
        remaining = obj.amount - total_paid - total_discounts
        
        if remaining <= 0:
            return format_html('<span style="color: green;">✓ Payée</span>')
        elif obj.due_date < timezone.now().date():
            return format_html('<span style="color: red;">⚠ En retard</span>')
        else:
            return format_html('<span style="color: orange;">⏳ En attente</span>')
    get_payment_status.short_description = "Statut"

@admin.register(TranchePayment)
class TranchePaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt', 'student', 'tranche', 'amount', 'mode', 'payment_date', 'created_by']
    list_filter = ['mode', 'payment_date', 'tranche__fee_structure__year', 'tranche__fee_structure__school_class']
    search_fields = ['receipt', 'student__first_name', 'student__last_name', 'student__matricule']
    readonly_fields = ['created_by', 'created_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Informations du paiement', {
            'fields': ('student', 'tranche', 'amount', 'mode', 'receipt', 'document')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(InscriptionPayment)
class InscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt', 'student', 'fee_structure', 'amount', 'mode', 'payment_date', 'created_by']
    list_filter = ['mode', 'payment_date', 'fee_structure__year', 'fee_structure__school_class']
    search_fields = ['receipt', 'student__first_name', 'student__last_name', 'student__matricule']
    readonly_fields = ['created_by', 'created_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Informations du paiement', {
            'fields': ('student', 'fee_structure', 'amount', 'mode', 'receipt', 'document')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(FeeDiscount)
class FeeDiscountAdmin(admin.ModelAdmin):
    list_display = ['student', 'tranche', 'amount', 'reason', 'granted_at', 'created_by']
    list_filter = ['granted_at', 'tranche__fee_structure__year', 'tranche__fee_structure__school_class']
    search_fields = ['student__first_name', 'student__last_name', 'student__matricule', 'reason']
    readonly_fields = ['created_by', 'granted_at']
    date_hierarchy = 'granted_at'
    
    fieldsets = (
        ('Informations de la remise', {
            'fields': ('student', 'tranche', 'amount', 'reason')
        }),
        ('Audit', {
            'fields': ('created_by', 'granted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Moratorium)
class MoratoriumAdmin(admin.ModelAdmin):
    list_display = ['student', 'tranche', 'amount', 'new_due_date', 'is_approved', 'requested_at']
    list_filter = ['is_approved', 'requested_at', 'tranche__fee_structure__year']
    search_fields = ['student__first_name', 'student__last_name', 'student__matricule', 'reason']
    readonly_fields = ['requested_at']
    date_hierarchy = 'requested_at'
    
    fieldsets = (
        ('Informations du moratoire', {
            'fields': ('student', 'tranche', 'amount', 'new_due_date', 'reason')
        }),
        ('Validation', {
            'fields': ('is_approved', 'approved_at'),
        }),
        ('Audit', {
            'fields': ('requested_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_moratoriums', 'reject_moratoriums']
    
    def approve_moratoriums(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_approved=True, approved_at=timezone.now())
        self.message_user(request, f"{updated} moratoire(s) approuvé(s) avec succès.")
    approve_moratoriums.short_description = "Approuver les moratoires sélectionnés"
    
    def reject_moratoriums(self, request, queryset):
        updated = queryset.update(is_approved=False, approved_at=None)
        self.message_user(request, f"{updated} moratoire(s) rejeté(s).")
    reject_moratoriums.short_description = "Rejeter les moratoires sélectionnés"

@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ['payment', 'amount', 'reason', 'refund_date', 'created_by']
    list_filter = ['refund_date', 'payment__mode']
    search_fields = ['payment__receipt', 'payment__student__first_name', 'payment__student__last_name', 'reason']
    readonly_fields = ['created_by', 'refund_date']
    date_hierarchy = 'refund_date'
    
    fieldsets = (
        ('Informations du remboursement', {
            'fields': ('payment', 'amount', 'reason')
        }),
        ('Audit', {
            'fields': ('created_by', 'refund_date'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ExtraFee)
class ExtraFeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'fee_type', 'amount', 'year', 'is_exam_fee', 'is_active', 'due_date', 'created_by']
    list_filter = ['fee_type', 'year', 'is_exam_fee', 'is_active', 'due_date', 'created_at']
    search_fields = ['name', 'description', 'fee_type__name']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'fee_type', 'description', 'year', 'due_date', 'is_optional', 'is_active')
        }),
        ('Gestion des classes', {
            'fields': ('apply_to_all_classes', 'classes')
        }),
        ('Gestion des examens', {
            'fields': ('is_exam_fee', 'exam_types'),
            'classes': ('collapse',)
        }),
        ('Montants', {
            'fields': ('amount', 'amounts_by_class')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ExtraFeeType)
class ExtraFeeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'get_extra_fees_count']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    
    def get_extra_fees_count(self, obj):
        return obj.extra_fees.count()
    get_extra_fees_count.short_description = "Nombre de frais"

@admin.register(ExtraFeePayment)
class ExtraFeePaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt', 'student', 'extra_fee', 'amount', 'mode', 'payment_date', 'created_by']
    list_filter = ['mode', 'payment_date', 'extra_fee__fee_type', 'extra_fee__year']
    search_fields = ['receipt', 'student__first_name', 'student__last_name', 'student__matricule', 'extra_fee__name']
    readonly_fields = ['created_by', 'created_at', 'receipt']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Informations du paiement', {
            'fields': ('student', 'extra_fee', 'amount', 'mode', 'receipt', 'notes', 'document')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# Configuration des permissions
class FinancesPermissions:
    """Permissions personnalisées pour l'app finances"""
    
    class Meta:
        permissions = [
            ("view_financial_dashboard", "Peut voir le tableau de bord financier"),
            ("manage_fee_structures", "Peut gérer les structures de frais"),
            ("manage_payments", "Peut gérer les paiements"),
            ("manage_discounts", "Peut gérer les remises"),
            ("manage_moratoriums", "Peut gérer les moratoires"),
            ("manage_refunds", "Peut gérer les remboursements"),
            ("manage_extra_fees", "Peut gérer les frais annexes"),
            ("print_receipts", "Peut imprimer les reçus"),
            ("view_financial_reports", "Peut voir les rapports financiers"),
        ]
