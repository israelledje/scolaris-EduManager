from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import ParentUser, ParentPaymentMethod
from students.models import Guardian, Student

class ParentLoginForm(forms.Form):
    """Formulaire de connexion pour les parents"""
    username = forms.CharField(
        label="Nom d'utilisateur ou adresse email",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nom d\'utilisateur ou adresse email',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Votre mot de passe',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        label="Se souvenir de moi",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        })
    )

class ParentRegistrationForm(forms.Form):
    """Formulaire d'inscription pour générer les comptes parents"""
    guardian_id = forms.ModelChoiceField(
        queryset=Guardian.objects.all(),
        label="Sélectionner le parent/tuteur",
        empty_label="Choisir un parent...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'guardian-select'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer seulement les guardians avec email
        self.fields['guardian_id'].queryset = Guardian.objects.filter(
            email__isnull=False
        ).exclude(email='')

    def clean_guardian_id(self):
        guardian = self.cleaned_data['guardian_id']
        
        # Vérifier que le guardian n'a pas déjà un compte
        if ParentUser.objects.filter(email=guardian.email).exists():
            raise ValidationError("Ce parent a déjà un compte dans le portail.")
        
        # Vérifier que l'email est valide
        if not guardian.email:
            raise ValidationError("Ce parent n'a pas d'email valide.")
        
        return guardian

class ParentProfileForm(forms.ModelForm):
    """Formulaire de modification du profil parent"""
    class Meta:
        model = ParentUser
        fields = ['first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Téléphone'
            }),
        }

class ParentPaymentMethodForm(forms.ModelForm):
    """Formulaire pour ajouter/modifier une méthode de paiement"""
    class Meta:
        model = ParentPaymentMethod
        fields = ['method_type', 'account_number', 'account_name', 'is_default']
        widgets = {
            'method_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'method-type'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Numéro de compte/téléphone'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nom du compte'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        method_type = cleaned_data.get('method_type')
        account_number = cleaned_data.get('account_number')
        
        if method_type and account_number:
            # Validation spécifique selon le type de méthode
            if method_type in ['OM', 'MOMO']:
                # Validation pour Orange Money et MTN Mobile Money
                if not account_number.startswith(('+225', '225', '0')):
                    raise ValidationError({
                        'account_number': 'Le numéro doit commencer par +225, 225 ou 0'
                    })
                if len(account_number.replace('+225', '').replace('225', '')) != 10:
                    raise ValidationError({
                        'account_number': 'Le numéro doit contenir 10 chiffres'
                    })
            elif method_type == 'CARD':
                # Validation pour les cartes bancaires
                if len(account_number) < 13 or len(account_number) > 19:
                    raise ValidationError({
                        'account_number': 'Le numéro de carte doit contenir entre 13 et 19 chiffres'
                    })
        
        return cleaned_data

class PaymentForm(forms.Form):
    """Formulaire pour effectuer un paiement"""
    payment_method = forms.ModelChoiceField(
        queryset=ParentPaymentMethod.objects.none(),
        label="Méthode de paiement",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'payment-method'
        })
    )
    amount = forms.DecimalField(
        label="Montant (FCFA)",
        min_value=100,
        max_digits=10,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Montant en FCFA',
            'min': '100'
        })
    )

    def __init__(self, *args, parent_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent_user:
            # Filtrer les méthodes de paiement actives du parent
            self.fields['payment_method'].queryset = ParentPaymentMethod.objects.filter(
                parent_user=parent_user,
                is_active=True
            )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError("Le montant doit être supérieur à 0")
        return amount

class StudentSearchForm(forms.Form):
    """Formulaire de recherche d'étudiants"""
    search = forms.CharField(
        required=False,
        label="Rechercher",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nom, prénom ou ID de l\'étudiant...',
            'id': 'student-search'
        })
    )

class NotificationFilterForm(forms.Form):
    """Formulaire de filtrage des notifications"""
    NOTIFICATION_TYPE_CHOICES = [
        ('', 'Tous les types'),
        ('BULLETIN', 'Bulletins'),
        ('PAYMENT', 'Paiements'),
        ('PAYMENT_SUCCESS', 'Paiements réussis'),
        ('PAYMENT_FAILED', 'Paiements échoués'),
        ('ACADEMIC', 'Académique'),
        ('FINANCIAL', 'Financier'),
        ('GENERAL', 'Général'),
    ]
    
    notification_type = forms.ChoiceField(
        choices=NOTIFICATION_TYPE_CHOICES,
        required=False,
        label="Type de notification",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'notification-type-filter'
        })
    )
    
    is_read = forms.ChoiceField(
        choices=[
            ('', 'Tous'),
            ('True', 'Lues'),
            ('False', 'Non lues'),
        ],
        required=False,
        label="Statut",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'notification-status-filter'
        })
    )
    
    search = forms.CharField(
        required=False,
        label="Rechercher",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Rechercher dans les notifications...',
            'id': 'notification-search'
        })
    )

class FinancialFilterForm(forms.Form):
    """Formulaire de filtrage financier"""
    STATUS_CHOICES = [
        ('', 'Tous les statuts'),
        ('PAID', 'Payé'),
        ('PARTIAL', 'Partiellement payé'),
        ('UNPAID', 'Non payé'),
        ('OVERDUE', 'En retard'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="Statut de paiement",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'payment-status-filter'
        })
    )
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        required=False,
        label="Étudiant",
        empty_label="Tous les étudiants",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'student-filter'
        })
    )
    
    min_amount = forms.DecimalField(
        required=False,
        label="Montant minimum",
        min_value=0,
        max_digits=10,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Montant min en FCFA',
            'min': '0'
        })
    )
    
    max_amount = forms.DecimalField(
        required=False,
        label="Montant maximum",
        min_value=0,
        max_digits=10,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Montant max en FCFA',
            'min': '0'
        })
    )

    def __init__(self, *args, parent_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent_user:
            # Filtrer les étudiants du parent
            from .services import ParentPortalService
            students = ParentPortalService.get_parent_students(parent_user)
            self.fields['student'].queryset = students

    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        
        if min_amount and max_amount and min_amount > max_amount:
            raise ValidationError("Le montant minimum ne peut pas être supérieur au montant maximum")
        
        return cleaned_data
