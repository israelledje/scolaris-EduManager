from django import forms
from django.core.exceptions import ValidationError
from .models import Teacher
from school.services import MatriculeService
from subjects.models import Subject
from school.models import SchoolYear

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'matricule', 'first_name', 'last_name', 'birth_date', 'birth_place',
            'gender', 'nationality', 'address', 'phone', 'email', 'main_subject',
            'photo'
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Laissez vide pour génération automatique'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'birth_place': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'main_subject': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les matières disponibles
        self.fields['main_subject'].queryset = Subject.objects.all()
        
        # Si c'est un nouveau teacher, pré-remplir le matricule si génération automatique
        if not self.instance.pk:
            auto_matricule = MatriculeService.generate_matricule('TEACHER')
            if auto_matricule:
                self.fields['matricule'].initial = auto_matricule
                self.fields['matricule'].widget.attrs['readonly'] = True
                self.fields['matricule'].help_text = "Matricule généré automatiquement. Décochez 'Génération automatique' dans les paramètres pour saisir manuellement."

    def clean_matricule(self):
        matricule = self.cleaned_data.get('matricule')
        if not matricule:
            # Générer automatiquement si vide
            matricule = MatriculeService.generate_matricule('TEACHER')
            if not matricule:
                raise ValidationError("Le matricule est obligatoire quand la génération automatique est désactivée.")
        
        # Vérifier l'unicité
        if matricule:
            existing = Teacher.objects.filter(matricule=matricule)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("Ce matricule existe déjà.")
        
        return matricule

    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier qu'une école existe
        from school.models import School
        if not School.objects.exists():
            raise ValidationError("Aucune école n'est configurée dans le système. Veuillez créer une école d'abord.")
        
        # Vérifier qu'une année scolaire active existe
        current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
        if not current_year:
            raise ValidationError("Aucune année scolaire active n'est configurée. Veuillez configurer une année scolaire.")
        
        return cleaned_data

    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        # S'assurer que l'école est définie (prendre la première disponible)
        if not teacher.school_id:
            from school.models import School
            school = School.objects.first()
            if school:
                teacher.school = school
            else:
                raise ValidationError("Aucune école disponible.")
        
        # S'assurer que l'année scolaire est définie
        if not teacher.year_id:
            current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
            if current_year:
                teacher.year = current_year
            else:
                raise ValidationError("Aucune année scolaire active disponible.")
        
        if commit:
            teacher.save()
        return teacher


class TeachingAssignmentForm(forms.ModelForm):
    class Meta:
        model = Teacher  # Temporaire - à ajuster selon le modèle
        fields = ['first_name']  # Temporaire
        
        
class TeachingAssignmentCoefForm(forms.ModelForm):
    class Meta:
        model = Teacher  # Temporaire - à ajuster selon le modèle  
        fields = ['first_name']  # Temporaire