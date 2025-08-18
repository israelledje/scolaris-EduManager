from django.db import models
from school.models import SchoolYear
from classes.models import SchoolClass
from students.models import Student
from authentication.models import User

# Create your models here.

class FeeStructure(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='fee_structures')
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='fee_structures')
    inscription_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Frais d'inscription")
    tuition_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Frais de scolarité total")
    tranche_count = models.PositiveIntegerField(default=3, verbose_name="Nombre de tranches")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.school_class} - {self.year}"

class FeeTranche(models.Model):
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='tranches')
    number = models.PositiveIntegerField(verbose_name="Numéro de tranche")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(verbose_name="Date d'échéance")

    class Meta:
        unique_together = ('fee_structure', 'number')
        ordering = ['fee_structure', 'number']

    def __str__(self):
        return f"Tranche {self.number} - {self.fee_structure}"

class Moratorium(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='moratoriums')
    tranche = models.ForeignKey(FeeTranche, on_delete=models.CASCADE, related_name='moratoriums')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant concerné")
    new_due_date = models.DateField(verbose_name="Nouvelle date d'échéance")
    reason = models.TextField(verbose_name="Motif du moratoire")
    is_approved = models.BooleanField(default=False, verbose_name="Validé par l'administration")
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_moratoriums', verbose_name="Approuvé par")

    def __str__(self):
        return f"Moratoire {self.student} - {self.tranche} ({self.amount} FCFA)"

# Paiement effectif par élève et par tranche
class TranchePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='tranche_payments')
    tranche = models.ForeignKey(FeeTranche, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    mode = models.CharField(max_length=30, choices=[('cash', 'Espèces'), ('cheque', 'Chèque'), ('mobile', 'Mobile Money'), ('virement', 'Virement')])
    receipt = models.CharField(max_length=50, blank=True)
    document = models.FileField(upload_to='finances/receipts/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.tranche} ({self.amount} FCFA)"

# Paiement des frais d'inscription
class InscriptionPayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='inscription_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='inscription_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    mode = models.CharField(max_length=30, choices=[('cash', 'Espèces'), ('cheque', 'Chèque'), ('mobile', 'Mobile Money'), ('virement', 'Virement')])
    receipt = models.CharField(max_length=50, blank=True)
    document = models.FileField(upload_to='finances/inscription_receipts/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'fee_structure')

    def __str__(self):
        return f"Inscription {self.student} - {self.fee_structure} ({self.amount} FCFA)"

# Remise ou bourse sur les frais
class FeeDiscount(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_discounts')
    tranche = models.ForeignKey(FeeTranche, on_delete=models.CASCADE, related_name='discounts', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    granted_at = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def __str__(self):
        return f"Remise {self.amount} - {self.student} ({self.tranche or 'Année'})"

# Remboursement ou annulation de paiement
class PaymentRefund(models.Model):
    payment = models.ForeignKey(TranchePayment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    refund_date = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def __str__(self):
        return f"Remboursement {self.amount} - {self.payment}"

# Frais annexes (examens, uniformes, activités, etc.)
class ExtraFeeType(models.Model):
    """Types de frais annexes prédéfinis"""
    name = models.CharField(max_length=100, verbose_name="Nom du type de frais")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Type de frais annexe"
        verbose_name_plural = "Types de frais annexes"
    
    def __str__(self):
        return self.name

# Modèle temporaire pour éviter les conflits de migration
class ExtraFee(models.Model):
    """Frais annexes avec gestion avancée par classe"""
    name = models.CharField(max_length=100, verbose_name="Nom du frais")
    fee_type = models.ForeignKey(ExtraFeeType, on_delete=models.CASCADE, related_name='extra_fees', verbose_name="Type de frais", null=True, blank=True)
    
    # Gestion des examens
    is_exam_fee = models.BooleanField(default=False, verbose_name="Frais d'examen")
    exam_types = models.JSONField(default=list, blank=True, verbose_name="Types d'examens", 
                                help_text="Liste des types d'examens (BEPC, Probatoire, Bac)")
    
    # Gestion des classes
    apply_to_all_classes = models.BooleanField(default=False, verbose_name="Appliquer à toutes les classes")
    classes = models.ManyToManyField(SchoolClass, blank=True, related_name='extra_fees', verbose_name="Classes concernées")
    
    # Montants
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant par défaut")
    amounts_by_class = models.JSONField(default=dict, blank=True, verbose_name="Montants par classe",
                                      help_text="Montants spécifiques par classe (classe_id: montant)")
    
    # Informations générales
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='extra_fees', verbose_name="Année scolaire")
    due_date = models.DateField(null=True, blank=True, verbose_name="Date d'échéance")
    is_optional = models.BooleanField(default=False, verbose_name="Facultatif")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Métadonnées
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Frais annexe"
        verbose_name_plural = "Frais annexes"
        ordering = ['name', 'year']
    
    def __str__(self):
        return f"{self.name} - {self.year}"
    
    def get_amount_for_class(self, school_class):
        """Retourne le montant pour une classe spécifique"""
        if self.apply_to_all_classes:
            return self.amount
        
        # Vérifier si la classe est concernée
        if not self.classes.filter(id=school_class.id).exists():
            return 0
        
        # Retourner le montant spécifique à la classe ou le montant par défaut
        return self.amounts_by_class.get(str(school_class.id), self.amount)
    
    def get_concerned_students(self):
        """Retourne tous les étudiants concernés par ce frais"""
        if self.apply_to_all_classes:
            return Student.objects.filter(current_class__year=self.year)
        else:
            return Student.objects.filter(current_class__in=self.classes.all(), current_class__year=self.year)

class ExtraFeePayment(models.Model):
    """Paiement des frais annexes"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='extra_fee_payments', verbose_name="Étudiant")
    extra_fee = models.ForeignKey(ExtraFee, on_delete=models.CASCADE, related_name='payments', verbose_name="Frais annexe")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé")
    payment_date = models.DateField(auto_now_add=True, verbose_name="Date de paiement")
    mode = models.CharField(max_length=30, choices=[
        ('cash', 'Espèces'), 
        ('cheque', 'Chèque'), 
        ('mobile', 'Mobile Money'), 
        ('virement', 'Virement')
    ], verbose_name="Mode de paiement")
    receipt = models.CharField(max_length=50, blank=True, verbose_name="Numéro de reçu")
    document = models.FileField(upload_to='finances/extra_fee_receipts/', null=True, blank=True, verbose_name="Document")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Métadonnées
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Paiement frais annexe"
        verbose_name_plural = "Paiements frais annexes"
        unique_together = ('student', 'extra_fee')
    
    def __str__(self):
        return f"{self.student} - {self.extra_fee} ({self.amount} FCFA)"
    
    def save(self, *args, **kwargs):
        # Générer automatiquement le numéro de reçu si vide
        if not self.receipt:
            # S'assurer que payment_date est défini
            if not self.payment_date:
                from django.utils import timezone
                self.payment_date = timezone.now().date()
            
            self.receipt = f"FRA-{self.extra_fee.id:04d}-{self.student.id:04d}-{self.payment_date.strftime('%Y%m%d')}"
        super().save(*args, **kwargs)
