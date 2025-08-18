from django import forms
from .models import AcademicPeriod, EvaluationSequence, Exam, Evaluation
from school.models import SchoolYear, School
from classes.models import SchoolClass
from subjects.models import Subject
from students.models import Student

# ==================== FORMULAIRES PÉRIODES ====================

class AcademicPeriodForm(forms.ModelForm):
    class Meta:
        model = AcademicPeriod
        fields = ['name', 'period_type', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'placeholder': "Ex: 1er Trimestre"
            }),
            'period_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-5 w-5 text-blue-600 transition'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.year = kwargs.pop('year', None)
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        if self.year:
            self.fields['year'] = forms.ModelChoiceField(
                queryset=SchoolYear.objects.filter(id=self.year.id),
                initial=self.year,
                widget=forms.HiddenInput()
            )
        if self.school:
            self.fields['school'] = forms.ModelChoiceField(
                queryset=School.objects.filter(id=self.school.id),
                initial=self.school,
                widget=forms.HiddenInput()
            )

# ==================== FORMULAIRES SÉQUENCES ====================

class EvaluationSequenceForm(forms.ModelForm):
    class Meta:
        model = EvaluationSequence
        fields = ['sequence']
        widgets = {
            'sequence': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            })
        }

    def __init__(self, *args, **kwargs):
        self.period = kwargs.pop('period', None)
        super().__init__(*args, **kwargs)
        if self.period:
            self.fields['period'] = forms.ModelChoiceField(
                queryset=AcademicPeriod.objects.filter(id=self.period.id),
                initial=self.period,
                widget=forms.HiddenInput()
            )

# ==================== FORMULAIRES EXAMENS ====================

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'exam_type', 'subject', 'school_class', 'sequence', 'max_score', 'coefficient', 'exam_date', 'duration', 'instructions']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'placeholder': "Ex: Contrôle de Mathématiques"
            }),
            'exam_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            }),
            'school_class': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            }),
            'sequence': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'min': 1,
                'max': 100,
                'step': 0.5
            }),
            'coefficient': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'min': 0.1,
                'max': 10,
                'step': 0.1
            }),
            'exam_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'type': 'date'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'min': 15,
                'max': 300,
                'step': 15
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'rows': 4,
                'placeholder': "Instructions pour les élèves..."
            }),
        }

    def __init__(self, *args, **kwargs):
        self.sequence = kwargs.pop('sequence', None)
        super().__init__(*args, **kwargs)
        if self.sequence:
            self.fields['sequence'].initial = self.sequence
            self.fields['sequence'].queryset = EvaluationSequence.objects.filter(id=self.sequence.id)

# ==================== FORMULAIRES NOTES ====================

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['score', 'remarks']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'min': 0,
                'max': 20,
                'step': 0.25
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'rows': 3,
                'placeholder': "Commentaires sur la performance..."
            }),
        }

class BulkEvaluationForm(forms.Form):
    """Formulaire pour saisir les notes en masse"""
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )

    def __init__(self, *args, **kwargs):
        self.students = kwargs.pop('students', [])
        super().__init__(*args, **kwargs)
        
        # Créer un champ pour chaque étudiant
        for student in self.students:
            field_name = f'note_{student.id}'
            self.fields[field_name] = forms.DecimalField(
                required=False,
                min_value=0,
                max_value=20,
                decimal_places=2,
                widget=forms.NumberInput(attrs={
                    'class': 'w-full px-3 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                    'placeholder': 'Note /20',
                    'step': 0.25
                })
            )

# ==================== FORMULAIRES FILTRES ====================

class ExamFilterForm(forms.Form):
    """Formulaire de filtrage des examens"""
    period = forms.ModelChoiceField(
        queryset=AcademicPeriod.objects.filter(is_active=True),
        required=False,
        empty_label="Toutes les périodes",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label="Toutes les matières",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.filter(is_active=True),
        required=False,
        empty_label="Toutes les classes",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    exam_type = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Exam.EXAM_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    ) 