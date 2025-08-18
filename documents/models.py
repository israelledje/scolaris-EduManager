from django.db import models
from students.models import Student
from authentication.models import User

class DocumentCategory(models.Model):
    """Catégorie de documents (Bulletin, Certificat, etc.)"""
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    is_required = models.BooleanField(default=False, verbose_name="Document obligatoire")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie de document"
        verbose_name_plural = "Catégories de documents"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class StudentDocument(models.Model):
    """Document d'un étudiant"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_documents', verbose_name="Étudiant")
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, verbose_name="Catégorie")
    title = models.CharField(max_length=200, verbose_name="Titre du document")
    file = models.FileField(upload_to='documents/students/', verbose_name="Fichier")
    description = models.TextField(blank=True, verbose_name="Description")
    is_valid = models.BooleanField(default=True, verbose_name="Document valide")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Date d'expiration")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents', verbose_name="Uploadé par")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'upload")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Document étudiant"
        verbose_name_plural = "Documents étudiants"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.student} - {self.title}"
    
    @property
    def is_expired(self):
        """Vérifie si le document est expiré"""
        if self.expiry_date:
            from datetime import date
            return date.today() > self.expiry_date
        return False
    
    @property
    def file_extension(self):
        """Retourne l'extension du fichier"""
        import os
        return os.path.splitext(self.file.name)[1].lower()
    
    @property
    def file_size_mb(self):
        """Retourne la taille du fichier en MB"""
        try:
            return round(self.file.size / (1024 * 1024), 2)
        except:
            return 0

class DocumentTemplate(models.Model):
    """Modèle de document pour génération automatique"""
    name = models.CharField(max_length=100, verbose_name="Nom du modèle")
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, verbose_name="Catégorie")
    template_file = models.FileField(upload_to='documents/templates/', verbose_name="Fichier modèle")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Modèle actif")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Modèle de document"
        verbose_name_plural = "Modèles de documents"
        ordering = ['name']
    
    def __str__(self):
        return self.name
