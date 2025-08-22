from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.core.validators import RegexValidator
from django.utils.crypto import get_random_string
import secrets
import string

# Import des modèles nécessaires
from students.models import Student, Guardian
from finances.models import FeeTranche, TranchePayment
from notes.models import Bulletin

class ParentUser(models.Model):
    """Modèle pour les utilisateurs parents du portail"""
    
    ROLE_CHOICES = [
        ('PARENT', 'Parent'),
        ('GUARDIAN', 'Tuteur'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Actif'),
        ('INACTIVE', 'Inactif'),
        ('SUSPENDED', 'Suspendu'),
    ]
    
    # Informations de base
    username = models.CharField(max_length=150, unique=True, verbose_name="Nom d'utilisateur")
    email = models.EmailField(unique=True, verbose_name="Adresse email")
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    phone = models.CharField(
        max_length=20, 
        verbose_name="Téléphone",
        validators=[
            RegexValidator(
                regex=r'^(\+237|237)?[0-9]{10}$',
                message='Format de téléphone invalide. Utilisez le format: +2376123456789'
            )
        ]
    )
    
    # Rôle et statut
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PARENT', verbose_name="Rôle")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name="Statut")
    
    # Authentification
    password_hash = models.CharField(max_length=255, verbose_name="Hash du mot de passe")
    is_active = models.BooleanField(default=True, verbose_name="Compte actif")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Dernière connexion")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Utilisateur Parent"
        verbose_name_plural = "Utilisateurs Parents"
        ordering = ['-date_joined']
        db_table = 'parents_portal_parentuser'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def set_password(self, password):
        """Définit le mot de passe hashé"""
        self.password_hash = make_password(password)
    
    def check_password(self, password):
        """Vérifie si le mot de passe est correct"""
        return check_password(password, self.password_hash)
    
    def generate_temporary_password(self):
        """Génère un mot de passe temporaire sécurisé"""
        # Générer un mot de passe de 12 caractères avec lettres, chiffres et symboles
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(12))
        return password
    
    def get_full_name(self):
        """Retourne le nom complet"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retourne le prénom"""
        return self.first_name
    
    def is_authenticated(self):
        """Vérifie si l'utilisateur est authentifié"""
        return self.is_active and self.status == 'ACTIVE'
    
    def get_guardian_profiles(self):
        """Retourne tous les profils de tuteur liés à cet utilisateur"""
        return self.guardian_profiles.all()
    
    def get_students(self):
        """Retourne tous les étudiants liés via les profils de tuteur"""
        students = []
        for guardian in self.guardian_profiles.all():
            students.append(guardian.student)
        return students
    
    def send_credentials_email(self, password):
        """Envoie les identifiants par email"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = "Vos identifiants de connexion - Portail Parents Scolaris"
            message = f"""
            Bonjour {self.get_full_name()},
            
            Votre compte a été créé avec succès sur le portail parents de Scolaris.
            
            Vos identifiants de connexion :
            - Nom d'utilisateur : {self.username}
            - Mot de passe temporaire : {password}
            
            IMPORTANT : Changez votre mot de passe après votre première connexion.
            
            Accédez au portail : {settings.SITE_URL}/parents/login/
            
            Cordialement,
            L'équipe Scolaris
            """
            
            return send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur envoi email: {e}")
            return False

class ParentStudentRelation(models.Model):
    """
    Relation entre un parent et un étudiant avec permissions spécifiques
    """
    RELATION_CHOICES = [
        ('FATHER', 'Père'),
        ('MOTHER', 'Mère'),
        ('TUTOR', 'Tuteur'),
        ('GUARDIAN', 'Responsable légal'),
        ('OTHER', 'Autre'),
    ]
    
    parent_user = models.ForeignKey(ParentUser, on_delete=models.CASCADE, related_name='student_relations')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='parent_relations')
    relation_type = models.CharField(max_length=20, choices=RELATION_CHOICES)
    is_active = models.BooleanField(default=True)
    can_view_academic = models.BooleanField(default=True)
    can_view_financial = models.BooleanField(default=True)
    can_make_payments = models.BooleanField(default=True)
    can_view_attendance = models.BooleanField(default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('parent_user', 'student')
        verbose_name = "Relation Parent-Étudiant"
        verbose_name_plural = "Relations Parent-Étudiant"
    
    def __str__(self):
        return f"{self.parent_user} - {self.student} ({self.get_relation_type_display()})"

class ParentPaymentMethod(models.Model):
    """
    Méthodes de paiement enregistrées par le parent
    """
    PAYMENT_METHOD_CHOICES = [
        ('OM', 'Orange Money'),
        ('MOMO', 'MTN Mobile Money'),
        ('CARD', 'Carte bancaire'),
        ('BANK', 'Virement bancaire'),
    ]
    
    parent_user = models.ForeignKey(ParentUser, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    account_number = models.CharField(max_length=50, blank=True)  # Numéro de téléphone pour OM/MOMO
    account_name = models.CharField(max_length=100, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Méthode de Paiement"
        verbose_name_plural = "Méthodes de Paiement"
    
    def __str__(self):
        return f"{self.parent_user} - {self.get_method_type_display()}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Désactiver les autres méthodes par défaut
            ParentPaymentMethod.objects.filter(parent_user=self.parent_user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class ParentPayment(models.Model):
    """
    Paiements effectués par les parents via le portail
    """
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours de traitement'),
        ('COMPLETED', 'Complété'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
    ]
    
    # Informations de base
    payment_id = models.CharField(max_length=50, unique=True, blank=True)
    parent_user = models.ForeignKey(ParentUser, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='parent_payments')
    tranche = models.ForeignKey(FeeTranche, on_delete=models.CASCADE, related_name='parent_payments')
    
    # Montants
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Méthode de paiement
    payment_method = models.ForeignKey(ParentPaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    method_type = models.CharField(max_length=20, choices=ParentPaymentMethod.PAYMENT_METHOD_CHOICES)
    
    # Statut et suivi
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    transaction_id = models.CharField(max_length=100, blank=True)  # ID de transaction externe
    receipt_url = models.URLField(blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Paiement Parent"
        verbose_name_plural = "Paiements Parents"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Paiement {self.payment_id} - {self.parent_user} pour {self.student}"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = self.generate_payment_id()
        if not self.total_amount:
            self.total_amount = self.amount + self.fees
        super().save(*args, **kwargs)
    
    def generate_payment_id(self):
        """Génère un ID unique pour le paiement"""
        while True:
            payment_id = f"PP{get_random_string(10, '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
            if not ParentPayment.objects.filter(payment_id=payment_id).exists():
                return payment_id
    
    def process_payment(self):
        """Traite le paiement et met à jour le statut"""
        try:
            # Logique de traitement selon la méthode de paiement
            if self.method_type in ['OM', 'MOMO']:
                # Simulation de traitement mobile money
                self.status = 'PROCESSING'
                self.save()
                
                # Ici, vous intégreriez l'API réelle d'Orange Money ou MTN
                # Pour l'instant, on simule un succès
                self.status = 'COMPLETED'
                self.completed_at = timezone.now()
                self.save()
                
                # Créer le paiement dans le système financier
                self.create_financial_payment()
                
                return True
            else:
                # Autres méthodes de paiement
                pass
                
        except Exception as e:
            self.status = 'FAILED'
            self.save()
            return False
    
    def create_financial_payment(self):
        """Crée le paiement correspondant dans le système financier"""
        try:
            TranchePayment.objects.create(
                student=self.student,
                tranche=self.tranche,
                amount=self.amount,
                mode=self.method_type.lower(),
                receipt=self.payment_id,
                created_by=None  # Paiement parent
            )
        except Exception as e:
            print(f"Erreur création paiement financier: {e}")

class ParentNotification(models.Model):
    """
    Notifications envoyées aux parents
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('GRADE', 'Nouvelle note'),
        ('BULLETIN', 'Bulletin disponible'),
        ('PAYMENT', 'Paiement reçu'),
        ('REMINDER', 'Rappel de paiement'),
        ('ATTENDANCE', 'Absence'),
        ('GENERAL', 'Information générale'),
    ]
    
    parent_user = models.ForeignKey(ParentUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    related_url = models.URLField(blank=True)
    
    # Statut
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notification Parent"
        verbose_name_plural = "Notifications Parents"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.parent_user} - {self.get_notification_type_display()}: {self.title}"
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

class ParentLoginSession(models.Model):
    """
    Sessions de connexion des parents pour la sécurité
    """
    parent_user = models.ForeignKey(ParentUser, on_delete=models.CASCADE, related_name='login_sessions')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Session de Connexion Parent"
        verbose_name_plural = "Sessions de Connexion Parents"
    
    def __str__(self):
        return f"{self.parent_user} - {self.ip_address} ({self.created_at})"
