from django import forms
from .models import Teacher, TeachingAssignment
from subjects.models import Subject
from classes.models import SchoolClass
from school.models import SchoolYear

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        exclude = ('created_by', 'updated_by')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

class TeachingAssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        subject_id = kwargs.pop('subject_id', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les enseignants selon l'école et l'année si disponibles
        if hasattr(self, 'instance') and self.instance and self.instance.pk:
            # Édition d'une affectation existante
            school_class = self.instance.school_class
            year = self.instance.year
        elif 'initial' in kwargs:
            # Création d'une nouvelle affectation
            school_class = kwargs['initial'].get('school_class')
            year = kwargs['initial'].get('year')
        else:
            school_class = None
            year = None
        
        # Filtrer les enseignants par école et année
        if school_class and year:
            self.fields['teacher'].queryset = Teacher.objects.filter(
                school=school_class.school,
                year=year,
                is_active=True
            )
        
        # Filtrer par matière si spécifiée
        if subject_id:
            try:
                subject = Subject.objects.get(pk=subject_id)
                # Filtrer les enseignants qui enseignent cette matière
                subject_teachers = subject.teachers.filter(
                    school=school_class.school if school_class else None,
                    year=year if year else None,
                    is_active=True
                )
                if subject_teachers.exists():
                    self.fields['teacher'].queryset = subject_teachers
                # Pré-sélectionner l'enseignant principal si défini
                main_teacher = subject_teachers.filter(main_subject=subject).first()
                if main_teacher:
                    self.fields['teacher'].initial = main_teacher.pk
            except Subject.DoesNotExist:
                pass

    class Meta:
        model = TeachingAssignment
        fields = ['subject', 'teacher', 'school_class', 'year', 'coefficient', 'hours_per_week']
        widgets = {
            'subject': forms.Select(attrs={'class': 'w-full border border-slate-300 rounded-lg px-3 py-2'}),
            'teacher': forms.Select(attrs={'class': 'w-full border border-slate-300 rounded-lg px-3 py-2'}),
            'school_class': forms.HiddenInput(),
            'year': forms.HiddenInput(),
            'coefficient': forms.NumberInput(attrs={'class': 'w-full border border-slate-300 rounded-lg px-3 py-2', 'min': 1}),
            'hours_per_week': forms.NumberInput(attrs={'class': 'w-full border border-slate-300 rounded-lg px-3 py-2', 'min': 0, 'step': 0.5}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Validation simplifiée - plus de logique complexe pour is_titulaire
        return cleaned_data

class TeachingAssignmentCoefForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        fields = ['coefficient', 'hours_per_week']
        widgets = {
            'coefficient': forms.NumberInput(attrs={'class': 'w-full border border-slate-300 rounded-lg px-3 py-2', 'min': 1}),
            'hours_per_week': forms.NumberInput(attrs={'class': 'w-full border border-slate-300 rounded-lg px-3 py-2', 'min': 0, 'step': 0.5}),
        }