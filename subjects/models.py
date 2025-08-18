from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Subject(models.Model):
    """
    Modèle représentant une matière enseignée dans l'établissement.
    
    Ce modèle définit les matières disponibles pour l'enseignement,
    avec leurs caractéristiques de base et leurs relations avec les enseignants.
    """
    
    GROUP_CHOICES = [
        (1, 'Groupe 1'),
        (2, 'Groupe 2'),
    ]
    
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name=_("Nom de la matière"),
        help_text=_("Nom complet de la matière (ex: Mathématiques, Français, Histoire)")
    )
    code = models.CharField(
        max_length=10, 
        unique=True, 
        blank=True, 
        null=True,
        verbose_name=_("Code de la matière"),
        help_text=_("Code court unique pour identifier la matière (ex: MATH, FR, HIST)")
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée de la matière et de ses objectifs")
    )
    group = models.PositiveIntegerField(
        choices=GROUP_CHOICES, 
        default=1, 
        verbose_name=_("Groupe"),
        help_text=_("Groupe de classification de la matière")
    )
    teachers = models.ManyToManyField(
        'teachers.Teacher', 
        blank=True, 
        related_name='subjects',
        verbose_name=_("Enseignants"),
        help_text=_("Enseignants qualifiés pour cette matière")
    )

    class Meta:
        verbose_name = _("Matière")
        verbose_name_plural = _("Matières")
        ordering = ['name']
        db_table = 'subjects_subject'

    def __str__(self):
        """Représentation textuelle de la matière"""
        return self.name

    def get_teacher_count(self):
        """Retourne le nombre d'enseignants qualifiés pour cette matière"""
        return self.teachers.count()

    def get_active_programs_count(self):
        """Retourne le nombre de programmes actifs pour cette matière"""
        return self.programs.filter(is_active=True).count()


class SubjectProgram(models.Model):
    """
    Modèle représentant le programme pédagogique d'une matière pour une classe spécifique.
    
    Ce modèle définit le contenu pédagogique, les objectifs et la structure
    d'enseignement d'une matière pour une classe donnée sur une année scolaire.
    
    Relations:
    - subject: La matière concernée
    - school_class: La classe cible
    - school_year: L'année scolaire
    - learning_units: Les unités d'apprentissage du programme
    """
    
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        related_name='programs',
        verbose_name=_("Matière"),
        help_text=_("Matière concernée par ce programme")
    )
    school_class = models.ForeignKey(
        'classes.SchoolClass', 
        on_delete=models.CASCADE, 
        related_name='subject_programs',
        verbose_name=_("Classe"),
        help_text=_("Classe cible pour ce programme")
    )
    school_year = models.ForeignKey(
        'school.SchoolYear', 
        on_delete=models.CASCADE, 
        related_name='subject_programs',
        verbose_name=_("Année scolaire"),
        help_text=_("Année scolaire d'application du programme")
    )
    
    # Structure et contenu du programme
    title = models.CharField(
        max_length=200,
        verbose_name=_("Titre du programme"),
        help_text=_("Titre descriptif du programme pédagogique")
    )
    description = models.TextField(
        verbose_name=_("Description générale"),
        help_text=_("Description détaillée des objectifs et de l'approche pédagogique")
    )
    objectives = models.TextField(
        verbose_name=_("Objectifs d'apprentissage"),
        help_text=_("Liste des objectifs généraux à atteindre par les élèves")
    )
    
    # Métadonnées du programme
    total_hours = models.PositiveIntegerField(
        verbose_name=_("Heures totales"),
        help_text=_("Nombre total d'heures prévues pour ce programme")
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('BEGINNER', 'Débutant'),
            ('INTERMEDIATE', 'Intermédiaire'),
            ('ADVANCED', 'Avancé'),
        ],
        default='INTERMEDIATE',
        verbose_name=_("Niveau de difficulté"),
        help_text=_("Niveau de difficulté du programme")
    )
    
    # Statut et gestion
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Programme actif"),
        help_text=_("Indique si ce programme est actuellement en cours d'utilisation")
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name=_("Programme approuvé"),
        help_text=_("Indique si ce programme a été approuvé par la direction")
    )
    
    # Métadonnées système
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    created_by = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_programs',
        verbose_name=_("Créé par"),
        help_text=_("Enseignant ayant créé ce programme")
    )
    
    class Meta:
        verbose_name = _("Programme de matière")
        verbose_name_plural = _("Programmes de matières")
        unique_together = ['subject', 'school_class', 'school_year']
        ordering = ['subject__name', 'school_class__name', 'school_year__annee']
        db_table = 'subjects_subject_program'

    def __str__(self):
        """Représentation textuelle du programme"""
        return f"Programme {self.subject.name} - {self.school_class.name} ({self.school_year})"

    def get_completion_percentage(self):
        """
        Calcule le pourcentage de completion du programme basé sur les leçons terminées.
        
        Returns:
            float: Pourcentage de completion (0-100)
        """
        total_lessons = sum(unit.lessons.count() for unit in self.learning_units.all())
        completed_lessons = sum(
            unit.lessons.filter(status='COMPLETED').count() 
            for unit in self.learning_units.all()
        )
        
        if total_lessons == 0:
            return 0.0
        
        return round((completed_lessons / total_lessons) * 100, 1)

    def get_remaining_hours(self):
        """
        Calcule le nombre d'heures restantes dans le programme.
        
        Returns:
            int: Nombre d'heures restantes
        """
        used_hours = sum(
            unit.lessons.filter(status__in=['COMPLETED', 'IN_PROGRESS']).count() * 1.5
            for unit in self.learning_units.all()
        )
        return max(0, self.total_hours - used_hours)

    def get_units_count(self):
        """Retourne le nombre d'unités d'apprentissage dans ce programme"""
        return self.learning_units.count()

    def get_lessons_count(self):
        """Retourne le nombre total de leçons planifiées dans ce programme"""
        return sum(unit.lessons.count() for unit in self.learning_units.all())


class LearningUnit(models.Model):
    """
    Modèle représentant une unité d'apprentissage dans un programme pédagogique.
    
    Une unité d'apprentissage est un bloc cohérent de contenu pédagogique
    qui peut être enseigné sur plusieurs leçons. Elle définit les objectifs,
    le contenu et la progression d'un aspect spécifique de la matière.
    
    Relations:
    - subject_program: Le programme parent
    - lessons: Les leçons associées à cette unité
    - prerequisites: Les unités préalables requises
    """
    
    subject_program = models.ForeignKey(
        SubjectProgram, 
        on_delete=models.CASCADE, 
        related_name='learning_units',
        verbose_name=_("Programme parent"),
        help_text=_("Programme pédagogique auquel appartient cette unité")
    )
    
    # Informations de base
    title = models.CharField(
        max_length=200, 
        verbose_name=_("Titre de l'unité"),
        help_text=_("Titre descriptif de l'unité d'apprentissage")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description détaillée du contenu et des objectifs de l'unité")
    )
    
    # Planification et durée
    estimated_hours = models.PositiveIntegerField(
        verbose_name=_("Heures estimées"),
        help_text=_("Nombre d'heures estimées pour couvrir cette unité")
    )
    order = models.PositiveIntegerField(
        verbose_name=_("Ordre"),
        help_text=_("Ordre de progression dans le programme (1 = première unité)")
    )
    
    # Contenu pédagogique
    key_concepts = models.TextField(
        blank=True,
        verbose_name=_("Concepts clés"),
        help_text=_("Liste des concepts principaux abordés dans cette unité")
    )
    skills_developed = models.TextField(
        blank=True,
        verbose_name=_("Compétences développées"),
        help_text=_("Compétences que les élèves développeront grâce à cette unité")
    )
    learning_objectives = models.TextField(
        blank=True,
        verbose_name=_("Objectifs d'apprentissage"),
        help_text=_("Objectifs spécifiques à atteindre par les élèves")
    )
    
    # Prérequis et progression
    prerequisites = models.ManyToManyField(
        'self', 
        blank=True, 
        verbose_name=_("Prérequis"),
        help_text=_("Unités d'apprentissage qui doivent être maîtrisées avant celle-ci")
    )
    
    # Statut et gestion
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Unité active"),
        help_text=_("Indique si cette unité est actuellement enseignée")
    )
    
    # Métadonnées système
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    
    class Meta:
        verbose_name = _("Unité d'apprentissage")
        verbose_name_plural = _("Unités d'apprentissage")
        ordering = ['order']
        db_table = 'subjects_learning_unit'

    def __str__(self):
        """Représentation textuelle de l'unité d'apprentissage"""
        return f"{self.title} ({self.subject_program.subject.name})"

    def get_completion_percentage(self):
        """
        Calcule le pourcentage de completion de cette unité.
        
        Returns:
            float: Pourcentage de completion (0-100)
        """
        total_lessons = self.lessons.count()
        if total_lessons == 0:
            return 0.0
        
        completed_lessons = self.lessons.filter(status='COMPLETED').count()
        return round((completed_lessons / total_lessons) * 100, 1)

    def get_lessons_count(self):
        """Retourne le nombre de leçons dans cette unité"""
        return self.lessons.count()

    def get_completed_lessons_count(self):
        """Retourne le nombre de leçons terminées dans cette unité"""
        return self.lessons.filter(status='COMPLETED').count()

    def get_next_lesson(self):
        """
        Retourne la prochaine leçon à enseigner dans cette unité.
        
        Returns:
            Lesson: Prochaine leçon ou None si toutes sont terminées
        """
        return self.lessons.filter(status='PLANNED').order_by('planned_date').first()

    def can_be_started(self):
        """
        Vérifie si cette unité peut être commencée (prérequis satisfaits).
        
        Returns:
            bool: True si l'unité peut être commencée
        """
        for prereq in self.prerequisites.all():
            if prereq.get_completion_percentage() < 100:
                return False
        return True


class Lesson(models.Model):
    """
    Modèle représentant une leçon planifiée dans une unité d'apprentissage.
    
    Une leçon est une session d'enseignement spécifique qui fait partie
    d'une unité d'apprentissage. Elle définit le contenu, les activités
    et les objectifs d'une séance de cours.
    
    Relations:
    - learning_unit: L'unité d'apprentissage parente
    - timetable_slot: Le créneau horaire associé
    - teacher: L'enseignant responsable
    - student_progress: Le suivi de progression des élèves
    """
    
    learning_unit = models.ForeignKey(
        LearningUnit, 
        on_delete=models.CASCADE, 
        related_name='lessons',
        verbose_name=_("Unité d'apprentissage"),
        help_text=_("Unité d'apprentissage à laquelle appartient cette leçon")
    )
    timetable_slot = models.ForeignKey(
        'classes.TimetableSlot', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name=_("Créneau horaire"),
        help_text=_("Créneau horaire réservé pour cette leçon (optionnel)")
    )
    teacher = models.ForeignKey(
        'teachers.Teacher', 
        on_delete=models.CASCADE, 
        related_name='lessons',
        verbose_name=_("Enseignant"),
        help_text=_("Enseignant responsable de cette leçon")
    )
    
    # Contenu de la leçon
    title = models.CharField(
        max_length=200, 
        verbose_name=_("Titre de la leçon"),
        help_text=_("Titre descriptif de la leçon")
    )
    objectives = models.TextField(
        verbose_name=_("Objectifs spécifiques"),
        help_text=_("Objectifs d'apprentissage spécifiques pour cette leçon")
    )
    activities = models.TextField(
        verbose_name=_("Activités prévues"),
        help_text=_("Description des activités et exercices prévus")
    )
    materials_needed = models.TextField(
        blank=True,
        verbose_name=_("Matériel nécessaire"),
        help_text=_("Liste du matériel et des ressources nécessaires")
    )
    
    # Planification et durée
    planned_duration = models.PositiveIntegerField(
        default=60,
        verbose_name=_("Durée prévue (minutes)"),
        help_text=_("Durée prévue de la leçon en minutes")
    )
    actual_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Durée effective (minutes)"),
        help_text=_("Durée effective de la leçon en minutes")
    )
    
    # Statut et progression
    STATUS_CHOICES = [
        ('PLANNED', 'Planifiée'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminée'),
        ('CANCELLED', 'Annulée'),
        ('POSTPONED', 'Reportée'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PLANNED',
        verbose_name=_("Statut"),
        help_text=_("Statut actuel de la leçon")
    )
    completion_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_("Pourcentage de réalisation"),
        help_text=_("Pourcentage de réalisation de la leçon (0-100)")
    )
    
    # Notes et commentaires
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Notes et commentaires de l'enseignant")
    )
    student_feedback = models.TextField(
        blank=True,
        verbose_name=_("Retour des élèves"),
        help_text=_("Retour et commentaires des élèves sur la leçon")
    )
    
    # Dates et planification
    planned_date = models.DateField(
        verbose_name=_("Date prévue"),
        help_text=_("Date prévue pour cette leçon")
    )
    actual_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name=_("Date effective"),
        help_text=_("Date effective de réalisation de la leçon")
    )
    
    # Métadonnées système
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    created_by = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_lessons',
        verbose_name=_("Créé par"),
        help_text=_("Enseignant ayant créé cette leçon")
    )
    
    class Meta:
        verbose_name = _("Leçon")
        verbose_name_plural = _("Leçons")
        ordering = ['planned_date', 'timetable_slot__period']
        db_table = 'subjects_lesson'

    def __str__(self):
        """Représentation textuelle de la leçon"""
        return f"{self.title} - {self.teacher} ({self.get_status_display()})"

    def get_student_count(self):
        """Retourne le nombre d'élèves dans la classe de cette leçon"""
        if self.timetable_slot:
            return self.timetable_slot.class_obj.students.count()
        # Si pas de créneau, essayer de récupérer la classe via l'unité d'apprentissage
        if self.learning_unit and self.learning_unit.subject_program:
            return self.learning_unit.subject_program.school_class.students.count()
        return 0

    def get_progress_count(self):
        """Retourne le nombre d'élèves ayant un suivi de progression"""
        return self.student_progress.count()

    def get_average_understanding(self):
        """
        Calcule la moyenne du niveau de compréhension des élèves.
        
        Returns:
            float: Moyenne du niveau de compréhension (1-5) ou 0 si aucun suivi
        """
        progress_list = self.student_progress.all()
        if not progress_list:
            return 0.0
        
        total_understanding = sum(p.understanding_level for p in progress_list)
        return round(total_understanding / len(progress_list), 1)

    def get_average_participation(self):
        """
        Calcule la moyenne du niveau de participation des élèves.
        
        Returns:
            float: Moyenne du niveau de participation (1-5) ou 0 si aucun suivi
        """
        progress_list = self.student_progress.all()
        if not progress_list:
            return 0.0
        
        total_participation = sum(p.participation for p in progress_list)
        return round(total_participation / len(progress_list), 1)

    def can_be_started(self):
        """
        Vérifie si la leçon peut être commencée.
        
        Returns:
            bool: True si la leçon peut être commencée
        """
        return (
            self.status == 'PLANNED' and 
            self.learning_unit.can_be_started() and
            self.planned_date <= timezone.now().date()
        )

    def start_lesson(self):
        """
        Marque la leçon comme commencée.
        
        Returns:
            bool: True si la leçon a été démarrée avec succès
        """
        if self.can_be_started():
            self.status = 'IN_PROGRESS'
            self.actual_date = timezone.now().date()
            self.save()
            return True
        return False

    def complete_lesson(self, completion_percentage=100):
        """
        Marque la leçon comme terminée.
        
        Args:
            completion_percentage (int): Pourcentage de réalisation (0-100)
        
        Returns:
            bool: True si la leçon a été terminée avec succès
        """
        if self.status in ['PLANNED', 'IN_PROGRESS']:
            self.status = 'COMPLETED'
            self.completion_percentage = completion_percentage
            self.actual_duration = self.planned_duration
            self.save()
            return True
        return False


class LessonProgress(models.Model):
    """
    Modèle représentant le suivi de progression d'un élève pour une leçon spécifique.
    
    Ce modèle permet de tracer la progression individuelle de chaque élève
    pour chaque leçon, incluant la compréhension, la participation et les retours.
    
    Relations:
    - lesson: La leçon concernée
    - student: L'élève concerné
    """
    
    lesson = models.ForeignKey(
        Lesson, 
        on_delete=models.CASCADE, 
        related_name='student_progress',
        verbose_name=_("Leçon"),
        help_text=_("Leçon concernée par ce suivi")
    )
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='lesson_progress',
        verbose_name=_("Élève"),
        help_text=_("Élève concerné par ce suivi")
    )
    
    # Évaluation de la compréhension et participation
    understanding_level = models.PositiveIntegerField(
        choices=[(i, f"Niveau {i}") for i in range(1, 6)],
        verbose_name=_("Niveau de compréhension"),
        help_text=_("Niveau de compréhension de l'élève (1=Faible, 5=Excellent)")
    )
    participation = models.PositiveIntegerField(
        choices=[(i, f"Niveau {i}") for i in range(1, 6)],
        verbose_name=_("Niveau de participation"),
        help_text=_("Niveau de participation de l'élève (1=Faible, 5=Excellent)")
    )
    
    # Réalisation des devoirs et travaux
    homework_completed = models.BooleanField(
        default=False,
        verbose_name=_("Devoirs réalisés"),
        help_text=_("Indique si l'élève a réalisé les devoirs associés")
    )
    homework_quality = models.PositiveIntegerField(
        choices=[(i, f"Niveau {i}") for i in range(1, 6)],
        null=True,
        blank=True,
        verbose_name=_("Qualité des devoirs"),
        help_text=_("Qualité du travail réalisé (1=Faible, 5=Excellent)")
    )
    
    # Notes et commentaires
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Notes générales sur la progression de l'élève")
    )
    teacher_feedback = models.TextField(
        blank=True,
        verbose_name=_("Retour de l'enseignant"),
        help_text=_("Retour et commentaires de l'enseignant pour cet élève")
    )
    student_feedback = models.TextField(
        blank=True,
        verbose_name=_("Retour de l'élève"),
        help_text=_("Retour et commentaires de l'élève sur la leçon")
    )
    
    # Métadonnées système
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    evaluated_by = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evaluated_progress',
        verbose_name=_("Évalué par"),
        help_text=_("Enseignant ayant évalué cette progression")
    )
    
    class Meta:
        verbose_name = _("Progression de l'élève")
        verbose_name_plural = _("Progressions des élèves")
        unique_together = ['lesson', 'student']
        ordering = ['student__last_name', 'student__first_name']
        db_table = 'subjects_lesson_progress'

    def __str__(self):
        """Représentation textuelle de la progression"""
        return f"{self.student} - {self.lesson} (Compréhension: {self.understanding_level}/5)"

    def get_overall_score(self):
        """
        Calcule un score global basé sur la compréhension et la participation.
        
        Returns:
            float: Score global sur 10
        """
        base_score = (self.understanding_level + self.participation) / 2
        
        # Bonus pour les devoirs
        if self.homework_completed:
            if self.homework_quality:
                base_score += (self.homework_quality / 10)
            else:
                base_score += 0.5
        
        return min(10.0, round(base_score, 1))

    def get_performance_level(self):
        """
        Détermine le niveau de performance de l'élève.
        
        Returns:
            str: Niveau de performance (Excellent, Bon, Moyen, Faible)
        """
        score = self.get_overall_score()
        if score >= 8.5:
            return "Excellent"
        elif score >= 7.0:
            return "Bon"
        elif score >= 5.0:
            return "Moyen"
        else:
            return "Faible"

    def needs_attention(self):
        """
        Détermine si l'élève nécessite une attention particulière.
        
        Returns:
            bool: True si l'élève nécessite une attention particulière
        """
        return (
            self.understanding_level <= 2 or
            self.participation <= 2 or
            not self.homework_completed
        )
