from django import forms
from .models import Student, StudentClassHistory, Guardian, StudentDocument

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

class StudentClassHistoryForm(forms.ModelForm):
    class Meta:
        model = StudentClassHistory
        fields = ['student', 'school_class', 'year', 'is_repeating']
        widgets = {
            'student': forms.HiddenInput(),
            'year': forms.Select(attrs={'class': 'form-select'}),
            'school_class': forms.Select(attrs={'class': 'form-select'}),
            'is_repeating': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ['name', 'relation', 'phone', 'email', 'profession', 'is_emergency_contact']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm',
                'placeholder': 'Nom complet du parent/tuteur'
            }),
            'relation': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm'
            }, choices=[
                ('', '-- Choisir la relation --'),
                ('Père', 'Père'),
                ('Mère', 'Mère'),
                ('Tuteur', 'Tuteur'),
                ('Tutrice', 'Tutrice'),
                ('Grand-père', 'Grand-père'),
                ('Grand-mère', 'Grand-mère'),
                ('Oncle', 'Oncle'),
                ('Tante', 'Tante'),
                ('Frère', 'Frère'),
                ('Sœur', 'Sœur'),
                ('Autre', 'Autre')
            ]),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm',
                'placeholder': 'Numéro de téléphone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm',
                'placeholder': 'Adresse email (optionnel)'
            }),
            'profession': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm',
                'placeholder': 'Profession (optionnel)'
            }),
            'is_emergency_contact': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 focus:ring-blue-500 border-slate-300 rounded'
            })
        } 