from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DIRECTION = 'DIRECTION', 'Direction'
        SURVEILLANCE = 'SURVEILLANCE', 'Surveillance'
        ELEVE = 'ELEVE', 'Élève'
        PROFESSEUR = 'PROFESSEUR', 'Professeur'
        PARENT = 'PARENT', 'Parent'
        SUPPORT_TECHNIQUE = 'SUPPORT_TECHNIQUE', 'Support Technique'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ELEVE,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
