from django import forms
from .models import StudentDocument, DocumentCategory

class StudentDocumentForm(forms.ModelForm):
    class Meta:
        model = StudentDocument
        fields = ['category', 'title', 'file', 'description', 'is_valid', 'expiry_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Titre du document'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'rows': 3,
                'placeholder': 'Description du document'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'type': 'date'
            }),
            'is_valid': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-slate-100 border-slate-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les catégories actives
        self.fields['category'].queryset = DocumentCategory.objects.all().order_by('name')
        
        # Rendre certains champs optionnels
        self.fields['description'].required = False
        self.fields['expiry_date'].required = False
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Vérifier la taille du fichier (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Le fichier ne doit pas dépasser 10MB.")
            
            # Vérifier l'extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            import os
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError("Format de fichier non autorisé. Utilisez PDF, DOC, DOCX, JPG ou PNG.")
        
        return file

class DocumentCategoryForm(forms.ModelForm):
    class Meta:
        model = DocumentCategory
        fields = ['name', 'description', 'is_required']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Nom de la catégorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
                'rows': 3,
                'placeholder': 'Description de la catégorie'
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-slate-100 border-slate-300 rounded focus:ring-blue-500 focus:ring-2'
            }),
        } 