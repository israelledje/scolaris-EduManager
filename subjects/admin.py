from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Subject, SubjectProgram, LearningUnit, Lesson, LessonProgress


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle Subject.
    
    Permet de gérer les matières enseignées avec leurs caractéristiques
    et leurs relations avec les enseignants.
    """
    
    list_display = [
        'name', 'code', 'group', 'get_teacher_count', 'get_active_programs_count'
    ]
    list_filter = ['group', 'teachers']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'code', 'description', 'group')
        }),
        ('Enseignants', {
            'fields': ('teachers',),
            'description': 'Sélectionnez les enseignants qualifiés pour cette matière'
        }),
    )
    
    def get_teacher_count(self, obj):
        """Affiche le nombre d'enseignants qualifiés"""
        count = obj.get_teacher_count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    get_teacher_count.short_description = 'Enseignants'
    
    def get_active_programs_count(self, obj):
        """Affiche le nombre de programmes actifs"""
        count = obj.get_active_programs_count()
        return format_html('<span style="color: #28a745;">{}</span>', count)
    get_active_programs_count.short_description = 'Programmes actifs'


@admin.register(SubjectProgram)
class SubjectProgramAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle SubjectProgram.
    
    Permet de gérer les programmes pédagogiques des matières
    pour chaque classe et année scolaire.
    """
    
    list_display = [
        'subject', 'school_class', 'school_year', 'difficulty_level', 
        'total_hours', 'is_active', 'is_approved', 'get_completion_percentage'
    ]
    list_filter = [
        'is_active', 'is_approved', 'difficulty_level', 'school_year', 'subject'
    ]
    search_fields = ['title', 'subject__name', 'school_class__name']
    ordering = ['subject__name', 'school_class__name', 'school_year__annee']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('subject', 'school_class', 'school_year', 'title')
        }),
        ('Contenu pédagogique', {
            'fields': ('description', 'objectives', 'difficulty_level')
        }),
        ('Planification', {
            'fields': ('total_hours',)
        }),
        ('Statut', {
            'fields': ('is_active', 'is_approved')
        }),
        ('Métadonnées', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def get_completion_percentage(self, obj):
        """Affiche le pourcentage de completion du programme"""
        percentage = obj.get_completion_percentage()
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 50 else '#dc3545'
        return format_html(
            '<span style="color: {};">{}%</span>', 
            color, 
            percentage
        )
    get_completion_percentage.short_description = 'Completion'
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde le modèle en définissant l'utilisateur créateur"""
        if not change:  # Nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LearningUnit)
class LearningUnitAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle LearningUnit.
    
    Permet de gérer les unités d'apprentissage dans les programmes
    pédagogiques avec leurs prérequis et objectifs.
    """
    
    list_display = [
        'title', 'subject_program', 'order', 'estimated_hours', 
        'is_active', 'get_completion_percentage', 'get_lessons_count'
    ]
    list_filter = ['is_active', 'subject_program__subject', 'subject_program__school_class']
    search_fields = ['title', 'description', 'key_concepts']
    ordering = ['subject_program__subject__name', 'order']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('subject_program', 'title', 'description', 'order')
        }),
        ('Planification', {
            'fields': ('estimated_hours', 'is_active')
        }),
        ('Contenu pédagogique', {
            'fields': ('key_concepts', 'skills_developed', 'learning_objectives')
        }),
        ('Prérequis', {
            'fields': ('prerequisites',),
            'description': 'Sélectionnez les unités qui doivent être maîtrisées avant celle-ci'
        }),
    )
    
    def get_completion_percentage(self, obj):
        """Affiche le pourcentage de completion de l'unité"""
        percentage = obj.get_completion_percentage()
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 50 else '#dc3545'
        return format_html(
            '<span style="color: {};">{}%</span>', 
            color, 
            percentage
        )
    get_completion_percentage.short_description = 'Completion'
    
    def get_lessons_count(self, obj):
        """Affiche le nombre de leçons dans l'unité"""
        count = obj.get_lessons_count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    get_lessons_count.short_description = 'Leçons'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle Lesson.
    
    Permet de gérer les leçons planifiées avec leur contenu,
    statut et progression.
    """
    
    list_display = [
        'title', 'learning_unit', 'teacher', 'planned_date', 'status',
        'completion_percentage', 'get_student_count', 'get_average_understanding'
    ]
    list_filter = [
        'status', 'learning_unit__subject_program__subject', 
        'teacher', 'planned_date'
    ]
    search_fields = ['title', 'objectives', 'teacher__last_name']
    ordering = ['-planned_date', 'learning_unit__subject_program__subject__name']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('learning_unit', 'timetable_slot', 'teacher', 'title')
        }),
        ('Contenu pédagogique', {
            'fields': ('objectives', 'activities', 'materials_needed')
        }),
        ('Planification', {
            'fields': ('planned_date', 'planned_duration', 'actual_duration')
        }),
        ('Statut et progression', {
            'fields': ('status', 'completion_percentage')
        }),
        ('Notes et commentaires', {
            'fields': ('notes', 'student_feedback'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'actual_date'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['actual_date']
    
    def get_student_count(self, obj):
        """Affiche le nombre d'élèves dans la classe"""
        count = obj.get_student_count()
        return format_html('<span style="color: #007cba;">{}</span>', count)
    get_student_count.short_description = 'Élèves'
    
    def get_average_understanding(self, obj):
        """Affiche la moyenne de compréhension des élèves"""
        avg = obj.get_average_understanding()
        if avg == 0:
            return format_html('<span style="color: #6c757d;">N/A</span>')
        
        color = '#28a745' if avg >= 4 else '#ffc107' if avg >= 3 else '#dc3545'
        return format_html(
            '<span style="color: {};">{}/5</span>', 
            color, 
            avg
        )
    get_average_understanding.short_description = 'Compréhension moy.'
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde le modèle en définissant l'utilisateur créateur"""
        if not change:  # Nouvelle création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """
    Interface d'administration pour le modèle LessonProgress.
    
    Permet de gérer le suivi de progression individuel des élèves
    pour chaque leçon avec leurs évaluations et commentaires.
    """
    
    list_display = [
        'student', 'lesson', 'understanding_level', 'participation',
        'homework_completed', 'get_overall_score', 'get_performance_level'
    ]
    list_filter = [
        'understanding_level', 'participation', 'homework_completed',
        'lesson__learning_unit__subject_program__subject'
    ]
    search_fields = [
        'student__last_name', 'student__first_name', 
        'lesson__title', 'lesson__teacher__last_name'
    ]
    ordering = ['student__last_name', 'student__first_name', '-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('lesson', 'student', 'evaluated_by')
        }),
        ('Évaluation', {
            'fields': ('understanding_level', 'participation')
        }),
        ('Devoirs et travaux', {
            'fields': ('homework_completed', 'homework_quality')
        }),
        ('Notes et commentaires', {
            'fields': ('notes', 'teacher_feedback', 'student_feedback')
        }),
    )
    
    def get_overall_score(self, obj):
        """Affiche le score global de l'élève"""
        score = obj.get_overall_score()
        color = '#28a745' if score >= 8 else '#ffc107' if score >= 6 else '#dc3545'
        return format_html(
            '<span style="color: {};">{}/10</span>', 
            color, 
            score
        )
    get_overall_score.short_description = 'Score global'
    
    def get_performance_level(self, obj):
        """Affiche le niveau de performance de l'élève"""
        level = obj.get_performance_level()
        color_map = {
            'Excellent': '#28a745',
            'Bon': '#17a2b8',
            'Moyen': '#ffc107',
            'Faible': '#dc3545'
        }
        color = color_map.get(level, '#6c757d')
        return format_html(
            '<span style="color: {};">{}</span>', 
            color, 
            level
        )
    get_performance_level.short_description = 'Niveau'


# Configuration de l'interface d'administration
admin.site.site_header = "Administration SCOLARIS - Gestion Pédagogique"
admin.site.site_title = "SCOLARIS Pédagogie"
admin.site.index_title = "Gestion des Matières et Programmes Pédagogiques"
