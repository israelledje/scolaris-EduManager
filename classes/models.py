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


class Attendance(models.Model):
    """
    Modèle simple pour le suivi des présences des élèves
    """
    STATUS_CHOICES = [
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('late', 'Retard'),
        ('excused', 'Absence justifiée'),
    ]
    
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Élève concerné par cette présence"
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Classe de l'élève"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Matière concernée"
    )
    date = models.DateField(help_text="Date de la présence")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='present',
        help_text="Statut de présence"
    )
    remark = models.TextField(
        blank=True,
        null=True,
        help_text="Remarque sur la présence"
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_attendances',
        help_text="Utilisateur qui a enregistré la présence"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'subject', 'date')
        ordering = ['-date', 'student__last_name']
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date} ({self.get_status_display()})"
    
    @classmethod
    def get_student_attendance_stats(cls, student, school_class, period='month'):
        """
        Calcule les statistiques de présence pour un élève
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now().date()
        
        if period == 'today':
            start_date = now
            end_date = now
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'month':
            start_date = now.replace(day=1)
            if now.month == 12:
                end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
        else:
            start_date = now - timedelta(days=30)
            end_date = now
        
        attendances = cls.objects.filter(
            student=student,
            school_class=school_class,
            date__range=[start_date, end_date]
        )
        
        total = attendances.count()
        present = attendances.filter(status='present').count()
        absent = attendances.filter(status='absent').count()
        late = attendances.filter(status='late').count()
        excused = attendances.filter(status='excused').count()
        
        attendance_rate = (present / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'attendance_rate': round(attendance_rate, 1)
        }


class Sanction(models.Model):
    """
    Modèle pour les sanctions disciplinaires
    """
    SANCTION_CHOICES = [
        ('avertissement', 'Avertissement'),
        ('retenue', 'Retenue'),
        ('exclusion', 'Exclusion temporaire'),
        ('conseil', 'Conseil de discipline'),
    ]
    
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='sanctions',
        help_text="Élève sanctionné"
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='sanctions',
        help_text="Classe de l'élève"
    )
    sanction_type = models.CharField(
        max_length=20,
        choices=SANCTION_CHOICES,
        help_text="Type de sanction"
    )
    reason = models.TextField(help_text="Motif de la sanction")
    sanction_date = models.DateField(help_text="Date de la sanction")
    duration = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Durée (pour retenue/exclusion)"
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_sanctions',
        help_text="Utilisateur qui a enregistré la sanction"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-sanction_date', 'student__last_name']
        verbose_name = "Sanction"
        verbose_name_plural = "Sanctions"
    
    def __str__(self):
        return f"{self.student} - {self.get_sanction_type_display()} - {self.sanction_date}"


class ParentConvocation(models.Model):
    """
    Modèle pour les convocations de parents
    """
    CONVOCATION_REASON_CHOICES = [
        ('comportement', 'Problème de comportement'),
        ('resultats', 'Résultats scolaires'),
        ('assiduite', 'Problème d\'assiduité'),
        ('autre', 'Autre motif'),
    ]
    
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='convocations',
        help_text="Élève concerné"
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='convocations',
        help_text="Classe de l'élève"
    )
    convocation_reason = models.CharField(
        max_length=20,
        choices=CONVOCATION_REASON_CHOICES,
        help_text="Motif de la convocation"
    )
    details = models.TextField(help_text="Détails de la convocation")
    proposed_datetime = models.DateTimeField(help_text="Date et heure proposées")
    meeting_person = models.CharField(
        max_length=100,
        help_text="Personne qui recevra les parents"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('confirmed', 'Confirmée'),
            ('completed', 'Effectuée'),
            ('cancelled', 'Annulée'),
        ],
        default='pending',
        help_text="Statut de la convocation"
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_convocations',
        help_text="Utilisateur qui a enregistré la convocation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-proposed_datetime', 'student__last_name']
        verbose_name = "Convocation parent"
        verbose_name_plural = "Convocations parents"
    
    def __str__(self):
        return f"{self.student} - {self.get_convocation_reason_display()} - {self.proposed_datetime}"