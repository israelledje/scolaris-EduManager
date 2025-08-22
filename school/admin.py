from django.contrib import admin
from .models import School, SchoolYear, YearClosure, EducationSystem, SchoolLevel, SchoolType, Ministry, RegionalDelegation, DocumentHeader, MatriculeSequence

@admin.register(EducationSystem)
class EducationSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(SchoolLevel)
class SchoolLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'system', 'order')
    list_filter = ('system',)
    search_fields = ('name',)
    ordering = ('system', 'order', 'name')

@admin.register(SchoolType)
class SchoolTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(Ministry)
class MinistryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'phone', 'email')
    search_fields = ('name', 'code')
    ordering = ('name',)

@admin.register(RegionalDelegation)
class RegionalDelegationAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'ministry', 'phone', 'email')
    list_filter = ('region', 'ministry')
    search_fields = ('name', 'region')
    ordering = ('region', 'name')

@admin.register(DocumentHeader)
class DocumentHeaderAdmin(admin.ModelAdmin):
    list_display = ('name', 'school_name', 'is_default', 'ministry', 'regional_delegation')
    list_filter = ('is_default', 'ministry', 'regional_delegation')
    search_fields = ('name', 'school_name')
    ordering = ('name',)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type', 'education_system', 'is_active')
    search_fields = ('name', 'code', 'address')
    list_filter = ('type', 'education_system', 'is_active')
    filter_horizontal = ('levels',)
    readonly_fields = ('created_at', 'updated_at')

    def has_delete_permission(self, request, obj=None):
        # Interdire la suppression de l'établissement
        return False

@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ('annee', 'statut')
    list_filter = ('statut',)
    search_fields = ('annee',)
    actions = ['set_annee_en_cours']

    def has_delete_permission(self, request, obj=None):
        # Interdire la suppression des années scolaires
        return False

    def set_annee_en_cours(self, request, queryset):
        SchoolYear.objects.update(statut='CLOTUREE')
        queryset.update(statut='EN_COURS')
        self.message_user(request, "L'année sélectionnée est maintenant en cours.")
    set_annee_en_cours.short_description = "Définir comme année en cours"

@admin.register(YearClosure)
class YearClosureAdmin(admin.ModelAdmin):
    list_display = ('annee', 'date_cloture', 'nouvelle_annee')
    search_fields = ('annee__annee', 'nouvelle_annee')

@admin.register(MatriculeSequence)
class MatriculeSequenceAdmin(admin.ModelAdmin):
    list_display = ('sequence_type', 'prefix', 'current_year', 'last_number', 'is_active')
    list_filter = ('sequence_type', 'current_year', 'is_active')
    search_fields = ('prefix', 'format_pattern')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['reset_sequence', 'generate_test_matricule']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('sequence_type', 'current_year', 'is_active')
        }),
        ('Configuration du matricule', {
            'fields': ('prefix', 'format_pattern', 'last_number')
        }),
        ('Informations système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def reset_sequence(self, request, queryset):
        """Action pour remettre à zéro les séquences sélectionnées"""
        for sequence in queryset:
            sequence.last_number = 0
            sequence.save()
        self.message_user(request, f"{queryset.count()} séquence(s) remise(s) à zéro.")
    reset_sequence.short_description = "Remettre à zéro les séquences sélectionnées"
    
    def generate_test_matricule(self, request, queryset):
        """Action pour générer un matricule de test"""
        if queryset.count() == 1:
            sequence = queryset.first()
            test_matricule = sequence.generate_matricule()
            self.message_user(request, f"Matricule de test généré: {test_matricule}")
        else:
            self.message_user(request, "Veuillez sélectionner une seule séquence pour générer un matricule de test.")
    generate_test_matricule.short_description = "Générer un matricule de test"
