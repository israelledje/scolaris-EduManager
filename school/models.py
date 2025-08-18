from django.db import models
from django.core.exceptions import ValidationError

# --------------------
# Système éducatif
# --------------------
class EducationSystem(models.Model):
    """
    Système éducatif (Francophone, Anglophone, etc.)
    """
    name = models.CharField(max_length=30, unique=True, verbose_name="Nom du système")
    code = models.CharField(max_length=10, unique=True, verbose_name="Code du système")
    
    class Meta:
        verbose_name = "Système éducatif"
        verbose_name_plural = "Systèmes éducatifs"
        ordering = ['name']
    
    def __str__(self):
        return self.name

# --------------------
# Niveau scolaire
# --------------------
class SchoolLevel(models.Model):
    """
    Niveau scolaire (Maternelle, Primaire, Secondaire, etc.)
    """
    name = models.CharField(max_length=50, verbose_name="Nom du niveau")
    system = models.ForeignKey(EducationSystem, on_delete=models.CASCADE, related_name='levels', verbose_name="Système éducatif")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    
    class Meta:
        unique_together = ('name', 'system')
        verbose_name = "Niveau scolaire"
        verbose_name_plural = "Niveaux scolaires"
        ordering = ['system', 'order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.system.name})"

# --------------------
# Type d'établissement
# --------------------
class SchoolType(models.Model):
    """
    Type d'établissement (Public, Privé, Confessionnel, etc.)
    """
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du type")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code du type")
    
    class Meta:
        verbose_name = "Type d'établissement"
        verbose_name_plural = "Types d'établissements"
        ordering = ['name']
    
    def __str__(self):
        return self.name

# --------------------
# Ministère de tutelle
# --------------------
class Ministry(models.Model):
    """
    Ministère de tutelle de l'établissement
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du ministère")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code du ministère")
    address = models.TextField(blank=True, verbose_name="Adresse")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    class Meta:
        verbose_name = "Ministère de tutelle"
        verbose_name_plural = "Ministères de tutelle"
        ordering = ['name']
    
    def __str__(self):
        return self.name

# --------------------
# Délégation régionale
# --------------------
class RegionalDelegation(models.Model):
    """
    Délégation régionale de tutelle
    """
    name = models.CharField(max_length=100, verbose_name="Nom de la délégation")
    region = models.CharField(max_length=50, verbose_name="Région")
    ministry = models.ForeignKey(Ministry, on_delete=models.CASCADE, related_name='delegations', verbose_name="Ministère de tutelle")
    address = models.TextField(blank=True, verbose_name="Adresse")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    class Meta:
        unique_together = ('name', 'region')
        verbose_name = "Délégation régionale"
        verbose_name_plural = "Délégations régionales"
        ordering = ['region', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.region}"

# --------------------
# En-tête de document
# --------------------
class DocumentHeader(models.Model):
    """
    En-tête pour les documents officiels de l'école
    """
    name = models.CharField(max_length=100, verbose_name="Nom de l'en-tête")
    is_default = models.BooleanField(default=False, verbose_name="En-tête par défaut")
    
    # Informations de l'école
    school_name = models.CharField(max_length=255, verbose_name="Nom de l'établissement")
    school_motto = models.CharField(max_length=200, blank=True, verbose_name="Devise de l'école")
    school_address = models.TextField(verbose_name="Adresse de l'école")
    school_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone de l'école")
    school_email = models.EmailField(blank=True, verbose_name="Email de l'école")
    school_website = models.URLField(blank=True, verbose_name="Site web de l'école")
    
    # Logos et signatures
    logo = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Logo de l'école")
    signature = models.ImageField(upload_to='signatures/', null=True, blank=True, verbose_name="Signature du directeur")
    stamp = models.ImageField(upload_to='stamps/', null=True, blank=True, verbose_name="Tampon de l'école")
    
    # Informations administratives
    ministry = models.ForeignKey(Ministry, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_headers', verbose_name="Ministère de tutelle")
    regional_delegation = models.ForeignKey(RegionalDelegation, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_headers', verbose_name="Délégation régionale")
    authorization_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro d'autorisation")
    creation_date = models.DateField(blank=True, null=True, verbose_name="Date de création")
    
    # Informations du directeur
    director_name = models.CharField(max_length=100, blank=True, verbose_name="Nom du directeur")
    director_title = models.CharField(max_length=100, blank=True, verbose_name="Titre du directeur")
    
    class Meta:
        verbose_name = "En-tête de document"
        verbose_name_plural = "En-têtes de documents"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'un seul en-tête par défaut
        if self.is_default:
            DocumentHeader.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

# --------------------
# Établissement scolaire
# --------------------
class School(models.Model):
    """
    Modèle principal représentant un établissement scolaire
    """
    # Informations de base
    name = models.CharField(max_length=255, verbose_name="Nom de l'établissement")
    code = models.CharField(max_length=20, unique=True, verbose_name="Code de l'établissement")
    
    # Type et système
    type = models.ForeignKey(SchoolType, on_delete=models.CASCADE, related_name='schools', verbose_name="Type d'établissement")
    education_system = models.ForeignKey(EducationSystem, on_delete=models.CASCADE, related_name='schools', verbose_name="Système éducatif")
    levels = models.ManyToManyField(SchoolLevel, related_name='schools', verbose_name="Niveaux enseignés")
    
    # Informations administratives
    ministry = models.ForeignKey(Ministry, on_delete=models.SET_NULL, null=True, blank=True, related_name='schools', verbose_name="Ministère de tutelle")
    regional_delegation = models.ForeignKey(RegionalDelegation, on_delete=models.SET_NULL, null=True, blank=True, related_name='schools', verbose_name="Délégation régionale")
    authorization_number = models.CharField(max_length=100, blank=True, verbose_name="Numéro d'autorisation")
    creation_date = models.DateField(blank=True, null=True, verbose_name="Date de création")
    
    # Informations de contact
    address = models.TextField(verbose_name="Adresse")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Site web")
    
    # En-tête par défaut
    default_header = models.ForeignKey(DocumentHeader, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_schools', verbose_name="En-tête par défaut")
    
    # Statut
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Établissement scolaire"
        verbose_name_plural = "Établissements scolaires"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_active_header(self):
        """Retourne l'en-tête actif pour cette école"""
        return self.default_header or DocumentHeader.objects.filter(is_default=True).first()

# --------------------
# Année scolaire
# --------------------
class SchoolYear(models.Model):
    STATUTS = [
        ('EN_COURS', 'En cours'),
        ('CLOTUREE', 'Clôturée'),
    ]

    annee = models.CharField(max_length=9, unique=True, verbose_name="Année scolaire")  # Format : "2024-2025"
    statut = models.CharField(max_length=10, choices=STATUTS, default='EN_COURS')

    class Meta:
        ordering = ['-annee']

    def __str__(self):
        return f"{self.annee} ({self.get_statut_display()})"

    def is_active(self):
        return self.statut == 'EN_COURS'

    @classmethod
    def get_active_year(cls):
        return cls.objects.filter(statut='EN_COURS').first()

    def close(self, nouvelle_annee: str):
        """Méthode utilitaire pour clôturer cette année."""
        if self.statut == 'CLOTUREE':
            raise ValidationError(f"L'année {self.annee} est déjà clôturée.")
        self.statut = 'CLOTUREE'
        self.save()
        YearClosure.objects.create(annee=self, nouvelle_annee=nouvelle_annee)

# --------------------
# Clôture d'une année
# --------------------
class YearClosure(models.Model):
    annee = models.OneToOneField(SchoolYear, on_delete=models.CASCADE, related_name='cloture')
    date_cloture = models.DateTimeField(auto_now_add=True)
    nouvelle_annee = models.CharField(max_length=9, verbose_name="Nouvelle année scolaire")

    def __str__(self):
        return f"Clôture de {self.annee.annee} → {self.nouvelle_annee}"

# --------------------
# Année scolaire en cours (singleton)
# --------------------
class CurrentSchoolYear(models.Model):
    year = models.OneToOneField(SchoolYear, on_delete=models.CASCADE, related_name='as_current')

    def __str__(self):
        return f"Année active : {self.year.annee}"

    @classmethod
    def get(cls):
        obj = cls.objects.select_related('year').first()
        if not obj:
            raise Exception("Aucune année scolaire active définie.")
        return obj.year

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'un seul objet
        if not self.pk and CurrentSchoolYear.objects.exists():
            raise ValidationError("Il ne peut y avoir qu'une seule année scolaire active.")
        super().save(*args, **kwargs)
