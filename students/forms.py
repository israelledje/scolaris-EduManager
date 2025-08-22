from django import forms
from django.core.exceptions import ValidationError
from .models import Student, Guardian
from school.services import MatriculeService
from classes.models import SchoolClass
from school.models import SchoolYear

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'matricule', 'first_name', 'last_name', 'birth_date', 'birth_place',
            'gender', 'nationality', 'address', 'phone', 'current_class',
            'photo', 'is_repeating'
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
            'current_class': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_repeating': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les classes selon l'année scolaire active
        current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
        if current_year:
            self.fields['current_class'].queryset = SchoolClass.objects.filter(
                year=current_year, is_active=True
            )
        
        # Si c'est un nouveau student, pré-remplir le matricule si génération automatique
        if not self.instance.pk:
            auto_matricule = MatriculeService.generate_matricule('STUDENT')
            if auto_matricule:
                self.fields['matricule'].initial = auto_matricule
                self.fields['matricule'].widget.attrs['readonly'] = True
                self.fields['matricule'].help_text = "Matricule généré automatiquement. Décochez 'Génération automatique' dans les paramètres pour saisir manuellement."

    def clean_matricule(self):
        matricule = self.cleaned_data.get('matricule')
        if not matricule:
            # Générer automatiquement si vide
            matricule = MatriculeService.generate_matricule('STUDENT')
            if not matricule:
                raise ValidationError("Le matricule est obligatoire quand la génération automatique est désactivée.")
        
        # Vérifier l'unicité
        if matricule:
            existing = Student.objects.filter(matricule=matricule)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError("Ce matricule existe déjà.")
        
        return matricule

    def save(self, commit=True):
        student = super().save(commit=False)
        
        # S'assurer que l'année scolaire est définie
        if not student.year_id:
            current_year = SchoolYear.objects.filter(statut='EN_COURS').first()
            if current_year:
                student.year = current_year
        
        if commit:
            student.save()
        return student


class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ['name', 'relation', 'phone', 'email', 'profession', 'is_emergency_contact']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'relation': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'is_emergency_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }