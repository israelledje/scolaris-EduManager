from django import forms
from .models import Subject, SubjectProgram, LearningUnit, Lesson
from classes.models import SchoolClass, TimetableSlot
from teachers.models import Teacher
from school.models import SchoolYear

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description']

class SubjectProgramForm(forms.ModelForm):
    """Formulaire pour la création et modification de programmes pédagogiques"""
    
    class Meta:
        model = SubjectProgram
        fields = [
            'subject', 'school_class', 'school_year', 'title', 'description', 
            'objectives', 'total_hours', 'difficulty_level', 'is_active', 'is_approved'
        ]
        widgets = {
            'subject': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionnez une matière'
            }),
            'school_class': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionnez une classe'
            }),
            'school_year': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionnez une année scolaire'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du programme pédagogique'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée du programme'
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Listez les objectifs d\'apprentissage (un par ligne)'
            }),
            'total_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre total d\'heures prévues',
                'min': 1
            }),
            'difficulty_level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_approved': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des labels
        self.fields['subject'].label = 'Matière'
        self.fields['school_class'].label = 'Classe'
        self.fields['school_year'].label = 'Année Scolaire'
        self.fields['title'].label = 'Titre du Programme'
        self.fields['description'].label = 'Description'
        self.fields['objectives'].label = 'Objectifs d\'Apprentissage'
        self.fields['total_hours'].label = 'Heures Totales'
        self.fields['difficulty_level'].label = 'Niveau de Difficulté'
        self.fields['is_active'].label = 'Programme Actif'
        self.fields['is_approved'].label = 'Programme Approuvé'
        
        # Ajout d'aide contextuelle
        self.fields['title'].help_text = 'Donnez un titre clair et descriptif au programme'
        self.fields['description'].help_text = 'Décrivez les objectifs généraux et l\'approche pédagogique'
        self.fields['objectives'].help_text = 'Listez les compétences et connaissances que les élèves doivent acquérir'
        self.fields['total_hours'].help_text = 'Estimez le temps total nécessaire pour couvrir tout le programme'
        self.fields['difficulty_level'].help_text = 'Choisissez le niveau adapté à la classe cible'
        
        # Validation personnalisée
        self.fields['total_hours'].min_value = 1
        self.fields['total_hours'].max_value = 1000

class LearningUnitForm(forms.ModelForm):
    """Formulaire pour la création et modification d'unités d'apprentissage"""
    
    class Meta:
        model = LearningUnit
        fields = [
            'subject_program', 'title', 'description', 'estimated_hours', 
            'order', 'key_concepts', 'skills_developed', 'learning_objectives', 'is_active'
        ]
        widgets = {
            'subject_program': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de l\'unité d\'apprentissage'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée de l\'unité'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Heures estimées',
                'min': 1
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ordre dans la progression',
                'min': 1
            }),
            'key_concepts': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Concepts clés abordés dans cette unité'
            }),
            'developed_skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Compétences développées'
            }),
            'learning_objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Objectifs d\'apprentissage spécifiques'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des labels
        self.fields['subject_program'].label = 'Programme Parent'
        self.fields['title'].label = 'Titre de l\'Unité'
        self.fields['description'].label = 'Description'
        self.fields['estimated_hours'].label = 'Heures Estimées'
        self.fields['order'].label = 'Ordre de Progression'
        self.fields['key_concepts'].label = 'Concepts Clés'
        self.fields['skills_developed'].label = 'Compétences Développées'
        self.fields['learning_objectives'].label = 'Objectifs d\'Apprentissage'
        self.fields['is_active'].label = 'Unité Active'
        
        # Aide contextuelle
        self.fields['title'].help_text = 'Nom de l\'unité (ex: "Les nombres entiers")'
        self.fields['description'].help_text = 'Explication détaillée du contenu de l\'unité'
        self.fields['estimated_hours'].help_text = 'Temps prévu pour cette unité'
        self.fields['order'].help_text = 'Position dans la progression (1, 2, 3...)'
        self.fields['key_concepts'].help_text = 'Notions principales abordées'
        self.fields['skills_developed'].help_text = 'Savoir-faire que les élèves acquerront'
        self.fields['learning_objectives'].help_text = 'Ce que l\'élève doit maîtriser à la fin'

class LessonForm(forms.ModelForm):
    """Formulaire pour la création et modification de leçons"""
    
    class Meta:
        model = Lesson
        fields = [
            'learning_unit', 'title', 'objectives', 'activities', 'materials_needed', 
            'planned_date', 'planned_duration', 'teacher', 'timetable_slot', 'status'
        ]
        widgets = {
            'learning_unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de la leçon'
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Objectifs spécifiques de la leçon'
            }),
            'activities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Activités et exercices prévus'
            }),
            'materials_needed': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Matériel et ressources nécessaires'
            }),
            'planned_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'planned_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Durée en minutes',
                'min': 15,
                'max': 480
            }),
            'teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
            'timetable_slot': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des labels
        self.fields['learning_unit'].label = 'Unité d\'Apprentissage'
        self.fields['title'].label = 'Titre de la Leçon'
        self.fields['objectives'].label = 'Objectifs de la Leçon'
        self.fields['activities'].label = 'Activités Préparées'
        self.fields['materials_needed'].label = 'Matériel Nécessaire'
        self.fields['planned_date'].label = 'Date Prévue'
        self.fields['planned_duration'].label = 'Durée (minutes)'
        self.fields['teacher'].label = 'Enseignant'
        self.fields['timetable_slot'].label = 'Créneau Horaire'
        self.fields['status'].label = 'Statut'
        
        # Aide contextuelle
        self.fields['title'].help_text = 'Titre clair de la leçon'
        self.fields['objectives'].help_text = 'Objectifs spécifiques à atteindre'
        self.fields['activities'].help_text = 'Exercices et travaux pratiques'
        self.fields['materials_needed'].help_text = 'Ressources et outils requis'
        self.fields['planned_date'].help_text = 'Quand la leçon doit avoir lieu'
        self.fields['planned_duration'].help_text = 'Temps estimé pour la leçon'
        self.fields['teacher'].help_text = 'Enseignant responsable'
        self.fields['timetable_slot'].help_text = 'Créneau dans l\'emploi du temps'
        self.fields['status'].help_text = 'État actuel de la leçon' 

class TimetableSlotForm(forms.ModelForm):
    """Formulaire pour créer/modifier un créneau horaire"""
    
    # Options pour les jours et périodes
    DAY_CHOICES = [
        (1, 'Lundi'),
        (2, 'Mardi'),
        (3, 'Mercredi'),
        (4, 'Jeudi'),
        (5, 'Vendredi'),
    ]
    
    PERIOD_CHOICES = [
        (1, '1ère heure (8h-9h)'),
        (2, '2ème heure (9h-10h)'),
        (3, '3ème heure (10h-11h)'),
        (4, '4ème heure (11h-12h)'),
        (5, '5ème heure (13h30-14h30)'),
        (6, '6ème heure (14h30-15h30)'),
        (7, '7ème heure (15h30-16h30)'),
        (8, '8ème heure (16h30-17h30)'),
    ]
    
    day = forms.ChoiceField(
        choices=DAY_CHOICES,
        label="Jour de la semaine",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        label="Période",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    duration = forms.IntegerField(
        min_value=1,
        max_value=4,
        initial=1,
        label="Durée (en heures)",
        help_text="Nombre d'heures consécutives pour ce créneau",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = TimetableSlot
        fields = ['subject', 'teacher', 'day', 'period', 'duration']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        school_class = kwargs.pop('school_class', None)
        super().__init__(*args, **kwargs)
        
        if school_class:
            # Filtrer les matières qui ont des programmes pour cette classe
            from .models import SubjectProgram
            program_subjects = SubjectProgram.objects.filter(
                school_class=school_class,
                is_active=True
            ).values_list('subject_id', flat=True)
            
            self.fields['subject'].queryset = Subject.objects.filter(
                id__in=program_subjects
            )
            
            # Filtrer les enseignants de l'école
            self.fields['teacher'].queryset = Teacher.objects.filter(
                school=school_class.school,
                year=school_class.year,
                is_active=True
            )

class TimetableBulkForm(forms.Form):
    """Formulaire pour affecter en masse des matières aux créneaux"""
    
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        label="Matière",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        label="Enseignant",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    hours_per_week = forms.IntegerField(
        min_value=1,
        max_value=8,
        initial=4,
        label="Heures par semaine",
        help_text="Nombre total d'heures à répartir sur la semaine",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Options de répartition
    REPARTITION_CHOICES = [
        ('balanced', 'Répartition équilibrée (1h par jour)'),
        ('concentrated', 'Répartition concentrée (2h par jour)'),
        ('custom', 'Répartition personnalisée'),
    ]
    
    repartition_type = forms.ChoiceField(
        choices=REPARTITION_CHOICES,
        label="Type de répartition",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    # Jours spécifiques pour la répartition personnalisée
    monday_hours = forms.IntegerField(
        min_value=0,
        max_value=4,
        initial=1,
        label="Lundi (heures)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    tuesday_hours = forms.IntegerField(
        min_value=0,
        max_value=4,
        initial=1,
        label="Mardi (heures)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    wednesday_hours = forms.IntegerField(
        min_value=0,
        max_value=4,
        initial=1,
        label="Mercredi (heures)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    thursday_hours = forms.IntegerField(
        min_value=0,
        max_value=4,
        initial=1,
        label="Jeudi (heures)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    friday_hours = forms.IntegerField(
        min_value=0,
        max_value=4,
        initial=1,
        label="Vendredi (heures)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        school_class = kwargs.pop('school_class', None)
        super().__init__(*args, **kwargs)
        
        if school_class:
            # Filtrer les matières qui ont des programmes pour cette classe
            from .models import SubjectProgram
            program_subjects = SubjectProgram.objects.filter(
                school_class=school_class,
                is_active=True
            ).values_list('subject_id', flat=True)
            
            self.fields['subject'].queryset = Subject.objects.filter(
                id__in=program_subjects
            )
            
            # Filtrer les enseignants de l'école
            self.fields['teacher'].queryset = Teacher.objects.filter(
                school=school_class.school,
                year=school_class.year,
                is_active=True
            )
    
    def clean(self):
        cleaned_data = super().clean()
        repartition_type = cleaned_data.get('repartition_type')
        hours_per_week = cleaned_data.get('hours_per_week')
        
        if repartition_type == 'custom':
            monday = cleaned_data.get('monday_hours', 0)
            tuesday = cleaned_data.get('tuesday_hours', 0)
            wednesday = cleaned_data.get('wednesday_hours', 0)
            thursday = cleaned_data.get('thursday_hours', 0)
            friday = cleaned_data.get('friday_hours', 0)
            
            total_custom = monday + tuesday + wednesday + thursday + friday
            
            if total_custom != hours_per_week:
                raise forms.ValidationError(
                    f"La somme des heures par jour ({total_custom}) doit être égale "
                    f"au total des heures par semaine ({hours_per_week})"
                )
        
        return cleaned_data 