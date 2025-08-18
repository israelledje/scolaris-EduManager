from django.db import models
from school.models import SchoolYear, School
from authentication.models import User
from subjects.models import Subject
import logging

# Configuration du logger
logger = logging.getLogger(__name__)


class Teacher(models.Model):
    SEX_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]

    matricule = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField()
    birth_place = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=SEX_CHOICES)
    nationality = models.CharField(max_length=50, default='Camerounaise')
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)
    photo = models.ImageField(upload_to='teachers/photos/', null=True, blank=True)
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teachers')
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='teachers')

    # La matière principale du prof (par exemple pour orientation ou préférence)
    main_subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='main_teachers'
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.last_name.upper()} {self.first_name} ({self.matricule})"

class TeachingAssignment(models.Model):
    """
    Modèle représentant l'affectation d'un enseignant à une classe pour une matière donnée.
    
    Ce modèle gère les affectations d'enseignants aux classes avec leurs coefficients et heures.
    Le professeur titulaire est géré séparément via le champ main_teacher de SchoolClass.
    
    Attributes:
        teacher: L'enseignant affecté (peut être null pour les affectations sans enseignant)
        subject: La matière enseignée
        school_class: La classe concernée
        year: L'année scolaire
        coefficient: Coefficient de la matière pour le calcul des moyennes
        hours_per_week: Nombre d'heures par semaine pour cette matière
    """
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.CASCADE, 
        related_name='assignments', 
        null=True, 
        blank=True,
        help_text="Enseignant affecté à cette classe pour cette matière"
    )
    subject = models.ForeignKey(
        Subject, 
        on_delete=models.CASCADE, 
        related_name='assignments',
        help_text="Matière enseignée"
    )
    school_class = models.ForeignKey(
        'classes.SchoolClass', 
        on_delete=models.CASCADE, 
        related_name='assignments',
        help_text="Classe concernée par cette affectation"
    )
    year = models.ForeignKey(
        SchoolYear, 
        on_delete=models.CASCADE, 
        related_name='teaching_assignments',
        help_text="Année scolaire de l'affectation"
    )
    
    coefficient = models.PositiveIntegerField(
        default=1,
        help_text="Coefficient de la matière pour le calcul des moyennes"
    )
    hours_per_week = models.FloatField(
        default=0,
        help_text="Nombre d'heures par semaine pour cette matière"
    )

    class Meta:
        unique_together = ('teacher', 'subject', 'school_class', 'year')
        verbose_name = "Affectation d'enseignement"
        verbose_name_plural = "Affectations d'enseignement"
        ordering = ['school_class', 'subject', 'teacher']

    def __str__(self):
        if self.teacher:
            if self.subject:
                return f"{self.teacher} - {self.subject} ({self.school_class}, {self.year})"
            else:
                return f"{self.teacher} - Matière non spécifiée ({self.school_class}, {self.year})"
        else:
            if self.subject:
                return f"Non assigné - {self.subject} ({self.school_class}, {self.year})"
            else:
                return f"Affectation incomplète ({self.school_class}, {self.year})"
    
    def clean(self):
        """
        Validation personnalisée du modèle.
        """
        from django.core.exceptions import ValidationError
        
        # Une affectation doit avoir une matière
        if not self.subject:
            raise ValidationError("Une affectation doit avoir une matière spécifique.")
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour la validation.
        """
        # Validation avant sauvegarde
        self.clean()
        super().save(*args, **kwargs)
