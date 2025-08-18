from django import forms
from .models import SchoolClass, Timetable, TimetableSlot
from school.models import SchoolLevel, EducationSystem
from students.models import Student

class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['name', 'level', 'year', 'school', 'capacity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition placeholder-gray-400',
                'placeholder': "Nom de la classe"
            }),
            'level': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            }),
            'year': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            }),
            'school': forms.Select(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-5 w-5 text-blue-600 transition'
            }),
        }

class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ['school_class', 'year', 'school', 'data']

class AssignStudentsForm(forms.Form):
    school_class = forms.ModelChoiceField(queryset=SchoolClass.objects.all(), label="Classe")
    students = forms.ModelMultipleChoiceField(queryset=Student.objects.filter(is_active=True), widget=forms.CheckboxSelectMultiple, label="Élèves à affecter")

class TimetableSlotForm(forms.ModelForm):
    """
    Formulaire pour ajouter ou éditer un créneau d'emploi du temps.
    """
    duration = forms.ChoiceField(
        choices=[(i, f"{i} période{'s' if i > 1 else ''}") for i in range(1, 5)],
        label="Durée (en périodes)",
        initial=1,
        widget=forms.Select(attrs={'class': 'w-full border rounded px-2 py-1'})
    )
    class Meta:
        model = TimetableSlot
        fields = ['subject', 'teacher', 'duration']
        widgets = {
            'subject': forms.Select(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'teacher': forms.Select(attrs={'class': 'w-full border rounded px-2 py-1'}),
        }

class SchoolLevelForm(forms.ModelForm):
    class Meta:
        model = SchoolLevel
        fields = ['name', 'system']

class EducationSystemForm(forms.ModelForm):
    class Meta:
        model = EducationSystem
        fields = ['name'] 