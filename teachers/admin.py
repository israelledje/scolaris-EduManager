from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Teacher, TeachingAssignment

User = get_user_model()

class HasUserAccountFilter(admin.SimpleListFilter):
    title = 'Compte utilisateur'
    parameter_name = 'has_user_account'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Avec compte'),
            ('no', 'Sans compte'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(user__isnull=False)
        if self.value() == 'no':
            return queryset.filter(user__isnull=True)
        return queryset

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'last_name', 'first_name', 'main_subject', 'user_account', 'is_active')
    list_filter = ('is_active', 'main_subject', 'year', HasUserAccountFilter)
    search_fields = ('matricule', 'last_name', 'first_name', 'email', 'user__username')
    ordering = ('last_name', 'first_name')
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'first_name', 'last_name', 'birth_date', 'birth_place', 'gender', 'nationality')
        }),
        ('Contact', {
            'fields': ('address', 'phone', 'email', 'photo')
        }),
        ('Compte utilisateur', {
            'fields': ('user',),
            'description': 'Lier cet enseignant à un compte utilisateur pour lui donner accès au système'
        }),
        ('Affectation', {
            'fields': ('school', 'year', 'main_subject', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    
    def user_account(self, obj):
        """Affiche l'état du compte utilisateur"""
        if obj.user:
            return format_html(
                '<span style="color: green;">✅ {}</span>',
                obj.user.username
            )
        else:
            return format_html(
                '<span style="color: red;">❌ Aucun compte</span>'
            )
    user_account.short_description = 'Compte utilisateur'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personnaliser le champ de sélection pour 'user'"""
        if db_field.name == "user":
            # Afficher seulement les utilisateurs PROFESSEUR sans profil lié
            kwargs["queryset"] = User.objects.filter(
                role='PROFESSEUR',
                teacher_profile__isnull=True
            )
            kwargs["empty_label"] = "Aucun compte utilisateur"
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    actions = ['create_user_accounts']
    
    def create_user_accounts(self, request, queryset):
        """Action pour créer des comptes utilisateurs pour les enseignants sélectionnés"""
        created_count = 0
        
        for teacher in queryset.filter(user__isnull=True):
            if not teacher.email:
                continue
                
            # Vérifier si un utilisateur avec cet email existe déjà
            if User.objects.filter(email=teacher.email).exists():
                continue
                
            # Générer un username unique
            base_username = f"{teacher.first_name.lower()}.{teacher.last_name.lower()}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Créer l'utilisateur
            user = User.objects.create(
                username=username,
                first_name=teacher.first_name,
                last_name=teacher.last_name,
                email=teacher.email,
                role='PROFESSEUR',
                is_active=True
            )
            
            # Mot de passe temporaire
            temp_password = f"temp{teacher.matricule}123"
            user.set_password(temp_password)
            user.save()
            
            # Lier l'enseignant
            teacher.user = user
            teacher.save()
            
            created_count += 1
        
        self.message_user(
            request,
            f'{created_count} compte(s) utilisateur créé(s) avec succès. '
            f'Mot de passe temporaire: temp[matricule]123'
        )
    
    create_user_accounts.short_description = "Créer des comptes utilisateurs pour les enseignants sélectionnés"

@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'school_class', 'year', 'coefficient', 'hours_per_week')
    list_filter = ('year', 'subject', 'school_class')
    search_fields = ('teacher__last_name', 'teacher__first_name', 'subject__name', 'school_class__name')
    ordering = ('year', 'school_class', 'subject', 'teacher')
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('teacher', 'subject', 'school_class', 'year')
        }),
        ('Teaching Configuration', {
            'fields': ('coefficient', 'hours_per_week')
        }),
    )
