from django.db import models
from school.models import SchoolYear, School, SchoolLevel
from django.conf import settings
from subjects.models import Subject
from django.db.models import JSONField  # 07/07/2025: Pour stocker les ids des matières enseignées
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

SEQUENCE_TRIMESTER_MAP = {
    1: ['S1', 'S2'],
    2: ['S3', 'S4'],
    3: ['S5', 'S6'],
}

class SchoolClass(models.Model):
    """
    Modèle représentant une classe scolaire.
    Ajout du champ subject_teached le 07/07/2025 :
    - Liste des ids des matières enseignées dans la classe (ArrayField)
    """
    name = models.CharField(max_length=50)  # 6e, 1ère, Terminale, Form 1...
    level = models.ForeignKey(SchoolLevel, on_delete=models.CASCADE, related_name='classes')
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='classes')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    capacity = models.PositiveIntegerField(default=0, verbose_name="Capacité d'accueil")
    is_active = models.BooleanField(default=True)
    main_teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='titular_classes'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subject_teached = JSONField(
      blank=True,
      default=list,
      help_text="Liste des ids des matières enseignées dans la classe."
  )

    class Meta:
        unique_together = ('name', 'level', 'year', 'school')
        verbose_name = "Classe scolaire"
        verbose_name_plural = "Classes scolaires"
        ordering = ['level', 'name', 'year']

    def __str__(self):
        return f"{self.name} - {self.level.name} - {self.year}"

    @property
    def student_count(self):
        """Retourne le nombre d'élèves actuellement dans cette classe."""
        return self.students.filter(is_active=True).count()
    
    @property
    def main_teacher_display(self):
        """
        Retourne le nom complet du professeur titulaire ou "Non assigné".
        
        Returns:
            str: Nom complet du professeur titulaire ou "Non assigné"
        """
        if self.main_teacher:
            return f"{self.main_teacher.last_name.upper()} {self.main_teacher.first_name}"
        return "Non assigné"
    
    def get_main_teacher(self):
        """
        Méthode pour récupérer le professeur titulaire de la classe.
        
        Returns:
            Teacher ou None si aucun professeur titulaire n'est affecté
        """
        return self.main_teacher


class Timetable(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='timetables')
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='timetables')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='timetables')
    data = models.JSONField(default=dict, blank=True)  # Clé : jour, valeur : liste de créneaux
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('school_class', 'year', 'school')

    def __str__(self):
        return f"Emploi du temps {self.school_class} - {self.year}"


class TimetableSlot(models.Model):
    """
    Représente un créneau horaire dans l'emploi du temps d'une classe pour une année scolaire donnée.
    Un créneau correspond à un jour, une heure, une matière et un enseignant.
    """
    DAY_CHOICES = [
        (1, 'Lundi'),
        (2, 'Mardi'),
        (3, 'Mercredi'),
        (4, 'Jeudi'),
        (5, 'Vendredi'),
        (6, 'Samedi'),
    ]

    class_obj = models.ForeignKey(
        'classes.SchoolClass', on_delete=models.CASCADE, related_name='timetable_slots',
        help_text="Classe concernée par ce créneau."
    )
    year = models.ForeignKey(
        'school.SchoolYear', on_delete=models.CASCADE, related_name='timetable_slots',
        help_text="Année scolaire du créneau."
    )
    day = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES, help_text="Jour de la semaine (1=Lundi, ...)."
    )
    period = models.PositiveSmallIntegerField(
        help_text="Index du créneau dans la journée (ex: 1=8h-9h, 2=9h-10h, ...)."
    )
    subject = models.ForeignKey(
        'subjects.Subject', on_delete=models.CASCADE, related_name='timetable_slots',
        help_text="Matière enseignée pendant ce créneau."
    )
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.CASCADE, related_name='timetable_slots',
        help_text="Enseignant affecté à ce créneau."
    )
    duration = models.PositiveSmallIntegerField(
        default=1,
        help_text="Nombre de périodes consécutives occupées par ce créneau (ex: 2 pour 2h)."
    )

    class Meta:
        unique_together = ('class_obj', 'year', 'day', 'period')
        ordering = ['day', 'period']

    def __str__(self):
        return f"{self.get_day_display()} {self.period} - {self.subject} ({self.teacher})"