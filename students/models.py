from django.db import models
from school.models import SchoolYear, School
from authentication.models import User
# -------------------- ÉLÈVES --------------------

class Student(models.Model):
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
    current_class = models.ForeignKey('classes.SchoolClass', on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    enrollment_date = models.DateField(auto_now_add=True)
    photo = models.ImageField(upload_to='students/photos/', null=True, blank=True)
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='students')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students')
    is_active = models.BooleanField(default=True)
    is_repeating = models.BooleanField(default=False, verbose_name="Redoublant")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.last_name.upper()} {self.first_name} ({self.matricule})"

    # --- MÉTHODES UTILITAIRES FINANCIÈRES ---
    def get_tranche_status(self, year):
        """
        Retourne pour chaque tranche : montant dû, payé, remise, reste à payer, statut (payé, partiel, en retard, à venir)
        """
        from finances.models import FeeTranche, TranchePayment, FeeDiscount
        import datetime

        if not self.current_class:
            return []
        tranches = FeeTranche.objects.filter(fee_structure__year=year, fee_structure__school_class=self.current_class)
        status = []
        today = datetime.date.today()
        for tranche in tranches:
            total_due = tranche.amount
            total_paid = TranchePayment.objects.filter(student=self, tranche=tranche).aggregate(models.Sum('amount'))['amount__sum'] or 0
            total_discount = FeeDiscount.objects.filter(student=self, tranche=tranche).aggregate(models.Sum('amount'))['amount__sum'] or 0
            reste = total_due - total_paid - total_discount
            if total_paid + total_discount >= total_due:
                etat = "Payé"
            elif tranche.due_date < today:
                etat = "En retard"
            elif total_paid > 0:
                etat = "Partiel"
            else:
                etat = "À venir"
            status.append({
                'tranche': tranche,
                'montant': total_due,
                'payé': total_paid,
                'remise': total_discount,
                'reste': max(reste, 0),
                'statut': etat,
                'échéance': tranche.due_date,
            })
        return status

    def get_total_paid(self, year):
        from finances.models import TranchePayment
        return TranchePayment.objects.filter(student=self, tranche__fee_structure__year=year).aggregate(models.Sum('amount'))['amount__sum'] or 0

    def get_total_due(self, year):
        from finances.models import FeeTranche
        if not self.current_class:
            return 0
        tranches = FeeTranche.objects.filter(fee_structure__year=year, fee_structure__school_class=self.current_class)
        return sum([t.amount for t in tranches])

    def get_total_discount(self, year):
        from finances.models import FeeDiscount
        return FeeDiscount.objects.filter(student=self, tranche__fee_structure__year=year).aggregate(models.Sum('amount'))['amount__sum'] or 0

    def get_total_remaining(self, year):
        return self.get_total_due(year) - self.get_total_paid(year) - self.get_total_discount(year)

class StudentClassHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='class_history')
    school_class = models.ForeignKey('classes.SchoolClass', on_delete=models.CASCADE)
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE)
    date_assigned = models.DateField(auto_now_add=True)
    is_repeating = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'school_class', 'year')

    def __str__(self):
        return f"{self.student} - {self.school_class} ({self.year})"

class Guardian(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='guardians')
    name = models.CharField(max_length=100)
    relation = models.CharField(max_length=50)  # Père, Mère, Tuteur, etc.
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True)
    is_emergency_contact = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.relation} de {self.student}"

class StudentDocument(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='students/documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.student}"

# -------------------- PAIEMENTS --------------------

class Payment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=100)  # Droit d'inscription, Scolarité, Examens...
    payment_date = models.DateField(auto_now_add=True)
    receipt_number = models.CharField(max_length=30, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.purpose} ({self.amount} FCFA)"

class Scholarship(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='scholarships')
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255)
    granted_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Bourse {self.amount} - {self.student} ({self.year})"

# -------------------- NOTES / ÉVALUATIONS --------------------

class Subject(models.Model):
    name = models.CharField(max_length=100)
    level = models.ForeignKey('school.SchoolLevel', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Evaluation(models.Model):
    SEQUENCE_CHOICES = [
        ('S1', 'Séquence 1'),
        ('S2', 'Séquence 2'),
        ('S3', 'Séquence 3'),
        ('S4', 'Séquence 4'),
        ('S5', 'Séquence 5'),
        ('S6', 'Séquence 6'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    sequence = models.CharField(max_length=2, choices=SEQUENCE_CHOICES)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject', 'sequence', 'year')

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.score}/{self.max_score})"

# -------------------- PRÉSENCES --------------------

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    present = models.BooleanField(default=True)
    reason = models.CharField(max_length=255, blank=True)
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    justificatif = models.FileField(upload_to='students/absences/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'date', 'year')

    def __str__(self):
        return f"{self.date} - {self.student} - {'Présent' if self.present else 'Absent'}"

# -------------------- DISCIPLINE --------------------

class Sanction(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    reason = models.TextField()
    sanction_type = models.CharField(max_length=100)  # Avertissement, Exclusion, Blâme, etc.
    issued_by = models.CharField(max_length=100)  # Nom de l'autorité
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sanction_type} - {self.student}"