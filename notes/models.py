from django.db import models
from school.models import SchoolYear, School
from authentication.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db import transaction
from teachers.models import TeachingAssignment
import logging

logger = logging.getLogger(__name__)

# ==================== GESTION DES TRIMESTRES ====================

class Trimester(models.Model):
    """Trimestre académique"""
    TRIMESTER_CHOICES = [
        ('1ER', '1er Trimestre'),
        ('2EME', '2ème Trimestre'), 
        ('3EME', '3ème Trimestre'),
    ]
    
    trimester = models.CharField(max_length=4, choices=TRIMESTER_CHOICES, verbose_name="Trimestre")
    year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='trimesters')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='trimesters')
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trimester', 'year', 'school')
        ordering = ['trimester']
        verbose_name = "Trimestre"
        verbose_name_plural = "Trimestres"

    def __str__(self):
        return f"{self.get_trimester_display()} - {self.year.annee}"

    @property
    def is_current(self):
        """Vérifie si le trimestre est en cours"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

# ==================== GESTION DES ÉVALUATIONS ====================

class Evaluation(models.Model):
    """Évaluation (EVAL1 à EVAL6)"""
    EVAL_CHOICES = [
        ('EVAL1', 'Évaluation 1 (1er Trimestre)'),
        ('EVAL2', 'Évaluation 2 (1er Trimestre)'),
        ('EVAL3', 'Évaluation 3 (2ème Trimestre)'),
        ('EVAL4', 'Évaluation 4 (2ème Trimestre)'),
        ('EVAL5', 'Évaluation 5 (3ème Trimestre)'),
        ('EVAL6', 'Évaluation 6 (3ème Trimestre)'),
    ]
    
    eval_type = models.CharField(max_length=5, choices=EVAL_CHOICES, verbose_name="Type d'évaluation")
    trimester = models.ForeignKey(Trimester, on_delete=models.CASCADE, related_name='evaluations')
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='evaluations')
    school_class = models.ForeignKey('classes.SchoolClass', on_delete=models.CASCADE, related_name='evaluations')
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=20, verbose_name="Note maximale")
    coefficient = models.DecimalField(max_digits=3, decimal_places=1, default=1.0, verbose_name="Coefficient")
    eval_date = models.DateField(verbose_name="Date de l'évaluation")
    duration = models.PositiveIntegerField(help_text="Durée en minutes", default=60, verbose_name="Durée")
    instructions = models.TextField(blank=True, help_text="Instructions pour l'évaluation")
    is_open = models.BooleanField(default=True, verbose_name="Ouverte pour saisie")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_evaluations')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('eval_type', 'trimester', 'subject', 'school_class')
        ordering = ['-eval_date']
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"

    def __str__(self):
        return f"{self.get_eval_type_display()} - {self.subject} - {self.school_class}"

    @property
    def is_closed(self):
        """Vérifie si l'évaluation est clôturée"""
        return not self.is_open

    @property
    def grades_count(self):
        """Nombre de notes saisies"""
        return self.grades.count()

    @property
    def average_score(self):
        """Moyenne des notes pour cette évaluation"""
        grades = self.grades.all()
        if grades.exists():
            total = sum(grade.score for grade in grades)
            return round(total / grades.count(), 2)
        return 0

    def close_evaluation(self):
        """Clôture l'évaluation"""
        self.is_open = False
        self.closed_at = timezone.now()
        self.save()

# ==================== GESTION DES NOTES ====================

class StudentGrade(models.Model):
    """Note d'un étudiant"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='grades')
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name="Note"
    )
    remarks = models.TextField(blank=True, help_text="Commentaires du professeur")
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_students')
    graded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'evaluation')
        ordering = ['-graded_at']
        verbose_name = "Note d'étudiant"
        verbose_name_plural = "Notes d'étudiants"

    def __str__(self):
        return f"{self.student} - {self.evaluation} ({self.score}/20)"

    @property
    def percentage(self):
        """Pourcentage de réussite"""
        return round((self.score / self.evaluation.max_score) * 100, 1)

    @property
    def is_success(self):
        """Note considérée comme réussie (≥ 10/20)"""
        return self.score >= 10

    @property
    def grade_letter(self):
        """Lettre de note (A, B, C, D, E)"""
        if self.score >= 16:
            return 'A'
        elif self.score >= 14:
            return 'B'
        elif self.score >= 12:
            return 'C'
        elif self.score >= 10:
            return 'D'
        else:
            return 'E'

# ==================== GESTION DES BULLETINS ====================

class Bulletin(models.Model):
    """Bulletin officiel d'un étudiant"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='bulletins')
    trimester = models.ForeignKey(Trimester, on_delete=models.CASCADE, related_name='bulletins')
    class_size = models.PositiveIntegerField(verbose_name="Effectif de la classe")
    student_rank = models.PositiveIntegerField(verbose_name="Rang de l'élève")
    class_average = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Moyenne de la classe")
    student_average = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Moyenne de l'élève")
    total_points = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Total des points")
    total_coefficients = models.PositiveIntegerField(verbose_name="Total des coefficients")
    success_rate = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Taux de réussite (%)")
    appreciation = models.TextField(blank=True, help_text="Appréciation générale")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_bulletins')
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé")
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bulletins')

    class Meta:
        unique_together = ('student', 'trimester')
        ordering = ['student_rank']
        verbose_name = "Bulletin"
        verbose_name_plural = "Bulletins"

    def __str__(self):
        return f"Bulletin {self.student} - {self.trimester}"

    @property
    def rank_percentage(self):
        """Pourcentage du rang (ex: 45ème sur 69 = 65.2%)"""
        if self.class_size > 0:
            return round((self.student_rank / self.class_size) * 100, 1)
        return 0

    @property
    def performance_level(self):
        """Niveau de performance"""
        if self.student_average >= 16:
            return "Excellent"
        elif self.student_average >= 14:
            return "Très Bien"
        elif self.student_average >= 12:
            return "Bien"
        elif self.student_average >= 10:
            return "Assez Bien"
        elif self.student_average >= 8:
            return "Passable"
        else:
            return "Insuffisant"

class BulletinLine(models.Model):
    """Ligne de matière dans un bulletin"""
    bulletin = models.ForeignKey(Bulletin, on_delete=models.CASCADE, related_name='lines')
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE)
    coefficient = models.DecimalField(max_digits=3, decimal_places=1, verbose_name="Coefficient")
    average = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Moyenne")
    total_points = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Total des points")
    max_coefficient_rank = models.DecimalField(max_digits=6, decimal_places=1, verbose_name="Max Coef Rangs")
    class_average_percent = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Moy. Cla %")
    appreciation = models.CharField(max_length=255, blank=True, help_text="Appréciation de la matière")

    class Meta:
        unique_together = ('bulletin', 'subject')
        verbose_name = "Ligne de bulletin"
        verbose_name_plural = "Lignes de bulletin"

    def __str__(self):
        return f"{self.subject} - {self.average}/20 (coef: {self.coefficient})"

    @property
    def is_success(self):
        """Matière réussie (≥ 10/20)"""
        return self.average >= 10

# ==================== UTILITAIRES ====================

class BulletinUtils:
    """Utilitaires pour la génération des bulletins"""
    
    @staticmethod
    def generate_bulletins_for_trimester(trimester_id):
        """Génère tous les bulletins pour un trimestre donné"""
        from students.models import Student
        from subjects.models import Subject
        
        trimester = Trimester.objects.get(id=trimester_id)
        students = Student.objects.filter(
            current_class__in=trimester.year.classes.all(),
            year=trimester.year,
            is_active=True
        ).order_by('last_name', 'first_name')
        
        result_data = []
        
        for student in students:
            # Calculer la moyenne par matière
            subject_averages = {}
            total_points = 0
            total_coefs = 0
            
            # Récupérer toutes les évaluations du trimestre
            evaluations = Evaluation.objects.filter(
                trimester=trimester,
                school_class=student.current_class
            ).select_related('subject')
            
            # Grouper par matière
            for eval in evaluations:
                subject = eval.subject
                grades = StudentGrade.objects.filter(
                    student=student,
                    evaluation=eval
                )
                
                if grades.exists():
                    if subject not in subject_averages:
                        subject_averages[subject] = []
                    subject_averages[subject].extend(grades)
            
            # Calculer la moyenne par matière
            for subject, grades in subject_averages.items():
                if grades:
                    # Récupérer le coefficient et l'enseignant depuis TeachingAssignment
                    teaching_assignment = TeachingAssignment.objects.filter(
                        subject=subject,
                        school_class=student.current_class,
                        year=trimester.year
                    ).select_related('teacher').first()
                    
                    real_coefficient = teaching_assignment.coefficient if teaching_assignment else 1.0
                    teacher_name = f"{teaching_assignment.teacher.last_name.upper()} {teaching_assignment.teacher.first_name}" if teaching_assignment and teaching_assignment.teacher else "Non assigné"
                    
                    # Calculer la moyenne pondérée par coefficient
                    total_score = sum(grade.score * real_coefficient for grade in grades)
                    total_coef = real_coefficient * len(grades)
                    moyenne = total_score / total_coef if total_coef > 0 else 0
                    
                    # Calculer la cote (lettre) basée sur le pourcentage
                    percentage = (moyenne / 20) * 100
                    if percentage >= 90:
                        cote = "A+"
                        appreciation = "Expert"
                    elif percentage >= 70:
                        cote = "A"
                        appreciation = "Acquis"
                    elif percentage >= 55:
                        cote = "B"
                        appreciation = "En cours d'acquisition"
                    elif percentage >= 30:
                        cote = "C"
                        appreciation = "Compétence moyennement acquise (CMA)"
                    else:
                        cote = "D"
                        appreciation = "Non acquis"
                    
                    subject_averages[subject] = {
                        'average': moyenne,
                        'coefficient': real_coefficient,
                        'total_points': moyenne * real_coefficient,
                        'grades': grades,
                        'teacher_name': teacher_name,
                        'cote': cote,
                        'appreciation': appreciation
                    }
                    total_points += moyenne * real_coefficient
                    total_coefs += real_coefficient
            
            # Calculer la moyenne générale
            moyenne_generale = total_points / total_coefs if total_coefs > 0 else 0
            
            result_data.append({
                'student': student,
                'moyenne_generale': moyenne_generale,
                'total_points': total_points,
                'total_coefs': total_coefs,
                'subject_averages': subject_averages
            })
        
        # Trier par moyenne générale (décroissant)
        result_data.sort(key=lambda x: x['moyenne_generale'], reverse=True)
        
        # Calculer la moyenne de classe et autres statistiques
        if result_data:
            moyenne_classe = sum(r['moyenne_generale'] for r in result_data) / len(result_data)
            class_size = len(result_data)
        else:
            moyenne_classe = 0
            class_size = 0
        
        # Calculer les statistiques par matière pour tous les étudiants
        subject_stats = {}
        for student_data in result_data:
            for subject, subject_data in student_data['subject_averages'].items():
                if subject not in subject_stats:
                    subject_stats[subject] = []
                subject_stats[subject].append(subject_data['average'])
        
        # Calculer les moyennes de classe par matière
        subject_class_averages = {}
        for subject, averages in subject_stats.items():
            subject_class_averages[subject] = sum(averages) / len(averages) if averages else 0
        
        # Créer les bulletins
        bulletins_created = []
        with transaction.atomic():
            for rank, data in enumerate(result_data, start=1):
                bulletin = Bulletin.objects.create(
                    student=data['student'],
                    trimester=trimester,
                    class_size=class_size,
                    student_rank=rank,
                    class_average=moyenne_classe,
                    student_average=data['moyenne_generale'],
                    total_points=data['total_points'],
                    total_coefficients=data['total_coefs'],
                    success_rate=0  # À calculer
                )
                
                # Créer les lignes du bulletin
                for subject, subject_data in data['subject_averages'].items():
                    # Calculer le pourcentage par rapport à la moyenne de classe
                    class_avg = subject_class_averages.get(subject, 0)
                    class_average_percent = 0
                    if class_avg > 0:
                        # Limiter le pourcentage à 100% maximum
                        percent = (subject_data['average'] / class_avg) * 100
                        class_average_percent = min(percent, 100)
                    
                    BulletinLine.objects.create(
                        bulletin=bulletin,
                        subject=subject,
                        coefficient=subject_data['coefficient'],
                        average=subject_data['average'],
                        total_points=subject_data['total_points'],
                        max_coefficient_rank=0,  # À calculer
                        class_average_percent=class_average_percent,
                        appreciation=subject_data['appreciation']
                    )
                
                # Stocker les données du bulletin pour les notifications
                bulletin_data = {
                    'student': data['student'],
                    'trimester': trimester,
                    'moyenne_generale': data['moyenne_generale'],
                    'class_average': moyenne_classe,
                    'rank': rank,
                    'class_size': class_size,
                    'subject_averages': data['subject_averages']
                }
                bulletins_created.append(bulletin_data)
        
        # Envoyer les notifications automatiques aux parents (en arrière-plan)
        try:
            from .services import bulletin_notification_service
            for bulletin_data in bulletins_created:
                try:
                    # Envoyer les notifications de manière asynchrone (simulation)
                    notification_results = bulletin_notification_service.send_bulletin_notifications(bulletin_data)
                    logger.info(f"Notifications de bulletin envoyées pour {bulletin_data['student']}: {notification_results}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi des notifications pour {bulletin_data['student']}: {e}")
        except ImportError:
            logger.warning("Service de notification de bulletin non disponible")
        except Exception as e:
            logger.error(f"Erreur générale lors de l'envoi des notifications: {e}")
        
        return len(result_data)

    @staticmethod
    def close_evaluation(evaluation_id):
        """Clôture une évaluation"""
        evaluation = Evaluation.objects.get(id=evaluation_id)
        evaluation.close_evaluation()
        return evaluation
