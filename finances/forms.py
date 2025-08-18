from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    FeeStructure, FeeTranche, TranchePayment, InscriptionPayment, FeeDiscount, 
    Moratorium, PaymentRefund, ExtraFee, ExtraFeeType, ExtraFeePayment
)
from school.models import SchoolYear, CurrentSchoolYear
from classes.models import SchoolClass
from students.models import Student
import logging

logger = logging.getLogger(__name__)

class FeeStructureForm(forms.ModelForm):
    """Formulaire pour la création/modification des structures de frais"""
    
    class Meta:
        model = FeeStructure
        fields = ['school_class', 'year', 'inscription_fee', 'tuition_total', 'tranche_count']
        widgets = {
            'inscription_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tuition_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tranche_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '12'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        school_class = cleaned_data.get('school_class')
        year = cleaned_data.get('year')
        
        # Vérifier qu'il n'y a pas déjà une structure pour cette classe et année
        if self.instance.pk is None:  # Nouvelle création
            if FeeStructure.objects.filter(school_class=school_class, year=year).exists():
                logger.warning(f"Tentative de création d'une structure de frais dupliquée pour {school_class} - {year}")
                raise ValidationError("Une structure de frais existe déjà pour cette classe et cette année scolaire.")
        
        return cleaned_data

class FeeTrancheForm(forms.ModelForm):
    """Formulaire pour la création/modification des tranches de paiement"""
    
    class Meta:
        model = FeeTranche
        fields = ['number', 'amount', 'due_date']
        widgets = {
            'number': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'placeholder': 'Numéro de la tranche'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir la date minimale à aujourd'hui
        today = timezone.now().date()
        self.fields['due_date'].widget.attrs['min'] = today.isoformat()

    def clean(self):
        cleaned_data = super().clean()
        fee_structure = cleaned_data.get('fee_structure')
        number = cleaned_data.get('number')
        amount = cleaned_data.get('amount')
        due_date = cleaned_data.get('due_date')
        
        if fee_structure and number:
            # Vérifier que le numéro de tranche n'existe pas déjà
            if self.instance.pk is None:  # Nouvelle création
                if FeeTranche.objects.filter(fee_structure=fee_structure, number=number).exists():
                    logger.warning(f"Tentative de création d'une tranche dupliquée: {number} pour {fee_structure}")
                    raise ValidationError(f"La tranche numéro {number} existe déjà pour cette structure de frais.")
            else:  # Modification
                if FeeTranche.objects.filter(fee_structure=fee_structure, number=number).exclude(pk=self.instance.pk).exists():
                    logger.warning(f"Tentative de modification vers un numéro de tranche dupliqué: {number} pour {fee_structure}")
                    raise ValidationError(f"La tranche numéro {number} existe déjà pour cette structure de frais.")
        
        if amount and amount <= 0:
            raise ValidationError("Le montant doit être supérieur à 0.")
        
        if due_date:
            today = timezone.now().date()
            if due_date < today:
                raise ValidationError("La date d'échéance doit être dans le futur.")
        
        return cleaned_data

class TranchePaymentForm(forms.ModelForm):
    """Formulaire pour l'enregistrement des paiements de tranches"""
    
    class Meta:
        model = TranchePayment
        fields = ['student', 'tranche', 'amount', 'mode', 'receipt', 'document']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mode': forms.Select(attrs={'class': 'form-control'}),
            'receipt': forms.TextInput(attrs={'class': 'form-control'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        tranche = cleaned_data.get('tranche')
        amount = cleaned_data.get('amount')
        
        if student and tranche and amount:
            # Vérifier que l'étudiant appartient à la classe de la structure de frais
            if student.current_class != tranche.fee_structure.school_class:
                logger.warning(f"Tentative de paiement pour un étudiant de classe différente: {student} - {tranche}")
                raise ValidationError("L'étudiant n'appartient pas à la classe de cette structure de frais.")
            
            # Vérifier que le montant ne dépasse pas le montant de la tranche
            if amount > tranche.amount:
                logger.warning(f"Tentative de paiement supérieur au montant de la tranche: {amount} > {tranche.amount}")
                raise ValidationError(f"Le montant payé ({amount}) ne peut pas dépasser le montant de la tranche ({tranche.amount}).")
        
        return cleaned_data

class InscriptionPaymentForm(forms.ModelForm):
    """Formulaire pour l'enregistrement des paiements de frais d'inscription"""
    
    class Meta:
        model = InscriptionPayment
        fields = ['student', 'fee_structure', 'amount', 'mode', 'receipt', 'document']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mode': forms.Select(attrs={'class': 'form-control'}),
            'receipt': forms.TextInput(attrs={'class': 'form-control'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        fee_structure = cleaned_data.get('fee_structure')
        amount = cleaned_data.get('amount')
        
        if student and fee_structure and amount:
            # Vérifier que l'étudiant appartient à la classe de la structure de frais
            if student.current_class != fee_structure.school_class:
                logger.warning(f"Tentative de paiement d'inscription pour un étudiant de classe différente: {student} - {fee_structure}")
                raise ValidationError("L'étudiant n'appartient pas à la classe de cette structure de frais.")
            
            # Vérifier que le montant ne dépasse pas le montant des frais d'inscription
            if amount > fee_structure.inscription_fee:
                logger.warning(f"Tentative de paiement d'inscription supérieur au montant défini: {amount} > {fee_structure.inscription_fee}")
                raise ValidationError(f"Le montant payé ({amount}) ne peut pas dépasser les frais d'inscription ({fee_structure.inscription_fee}).")
            
            # Vérifier qu'il n'y a pas déjà un paiement d'inscription pour cet étudiant et cette structure
            if self.instance.pk is None:  # Nouvelle création
                if InscriptionPayment.objects.filter(student=student, fee_structure=fee_structure).exists():
                    logger.warning(f"Tentative de paiement d'inscription dupliqué: {student} - {fee_structure}")
                    raise ValidationError("Un paiement d'inscription existe déjà pour cet étudiant et cette structure de frais.")
        
        return cleaned_data

class FeeDiscountForm(forms.ModelForm):
    """Formulaire pour l'attribution des remises/bourses"""
    
    class Meta:
        model = FeeDiscount
        fields = ['student', 'tranche', 'amount', 'reason']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        tranche = cleaned_data.get('tranche')
        amount = cleaned_data.get('amount')
        
        if student and tranche and amount:
            # Vérifier que l'étudiant appartient à la classe de la structure de frais
            if student.current_class != tranche.fee_structure.school_class:
                logger.warning(f"Tentative de remise pour un étudiant de classe différente: {student} - {tranche}")
                raise ValidationError("L'étudiant n'appartient pas à la classe de cette structure de frais.")
            
            # Vérifier que le montant de la remise ne dépasse pas le montant de la tranche
            if amount > tranche.amount:
                logger.warning(f"Tentative de remise supérieure au montant de la tranche: {amount} > {tranche.amount}")
                raise ValidationError(f"Le montant de la remise ({amount}) ne peut pas dépasser le montant de la tranche ({tranche.amount}).")
        
        return cleaned_data

class MoratoriumForm(forms.ModelForm):
    """Formulaire pour la demande de moratoire"""
    
    class Meta:
        model = Moratorium
        fields = ['student', 'tranche', 'amount', 'new_due_date', 'reason']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'new_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        tranche = cleaned_data.get('tranche')
        amount = cleaned_data.get('amount')
        new_due_date = cleaned_data.get('new_due_date')
        
        if student and tranche and amount:
            # Vérifier que l'étudiant appartient à la classe de la structure de frais
            if student.current_class != tranche.fee_structure.school_class:
                logger.warning(f"Tentative de moratoire pour un étudiant de classe différente: {student} - {tranche}")
                raise ValidationError("L'étudiant n'appartient pas à la classe de cette structure de frais.")
            
            # Vérifier que le montant ne dépasse pas le montant de la tranche
            if amount > tranche.amount:
                logger.warning(f"Tentative de moratoire supérieur au montant de la tranche: {amount} > {tranche.amount}")
                raise ValidationError(f"Le montant du moratoire ({amount}) ne peut pas dépasser le montant de la tranche ({tranche.amount}).")
        
        if new_due_date and new_due_date <= timezone.now().date():
            raise ValidationError("La nouvelle date d'échéance doit être postérieure à aujourd'hui.")
        
        return cleaned_data

class PaymentRefundForm(forms.ModelForm):
    """Formulaire pour les remboursements de paiements"""
    
    class Meta:
        model = PaymentRefund
        fields = ['payment', 'amount', 'reason']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment = cleaned_data.get('payment')
        amount = cleaned_data.get('amount')
        
        if payment and amount:
            # Vérifier que le montant du remboursement ne dépasse pas le montant payé
            if amount > payment.amount:
                logger.warning(f"Tentative de remboursement supérieur au montant payé: {amount} > {payment.amount}")
                raise ValidationError(f"Le montant du remboursement ({amount}) ne peut pas dépasser le montant payé ({payment.amount}).")
        
        return cleaned_data

class ExtraFeeTypeForm(forms.ModelForm):
    """Formulaire pour créer/éditer un type de frais annexe"""
    
    class Meta:
        model = ExtraFeeType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Ex: Bus Scolaire, Frais d\'examens, Uniformes...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Description détaillée du type de frais...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
            })
        }

class ExtraFeeForm(forms.ModelForm):
    """Formulaire pour créer/éditer un frais annexe"""
    
    # Champs pour la gestion des classes
    apply_to_all_classes = forms.BooleanField(
        required=False,
        label="Appliquer à toutes les classes",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500',
            'onchange': 'toggleClassSelection()'
        })
    )
    
    classes = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.none(),
        required=False,
        label="Classes concernées",
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'multiple': 'multiple',
            'id': 'id_classes'
        })
    )
    
    # Champs pour les examens
    is_exam_fee = forms.BooleanField(
        required=False,
        label="Frais d'examen",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500',
            'onchange': 'toggleExamOptions()'
        })
    )
    
    exam_types = forms.MultipleChoiceField(
        choices=[
            ('BEPC', 'BEPC'),
            ('Probatoire', 'Probatoire'),
            ('Baccalauréat', 'Baccalauréat'),
            ('CAP', 'CAP'),
            ('BTS', 'BTS'),
            ('Licence', 'Licence'),
            ('Master', 'Master')
        ],
        required=False,
        label="Types d'examens",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
        })
    )
    
    class Meta:
        model = ExtraFee
        fields = [
            'name', 'fee_type', 'is_exam_fee', 'exam_types', 'apply_to_all_classes', 
            'classes', 'amount', 'due_date', 'is_optional', 'description', 'year'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Ex: Frais d\'examen BEPC, Transport scolaire...'
            }),
            'fee_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'date'
            }),
            'is_optional': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Description détaillée du frais...'
            }),
            'year': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les classes par année scolaire actuelle et initialiser l'année
        try:
            current_year = CurrentSchoolYear.objects.first()
            if current_year:
                # Initialiser l'année scolaire avec l'année actuelle
                self.fields['year'].initial = current_year.year
                self.fields['year'].queryset = SchoolYear.objects.filter(id=current_year.year.id)
                # Filtrer les classes par année scolaire actuelle
                self.fields['classes'].queryset = SchoolClass.objects.filter(year=current_year.year)
            else:
                # Si pas d'année actuelle, utiliser toutes les classes
                self.fields['classes'].queryset = SchoolClass.objects.all()
        except Exception as e:
            # En cas d'erreur, utiliser toutes les classes
            self.fields['classes'].queryset = SchoolClass.objects.all()
    
    def clean(self):
        cleaned_data = super().clean()
        apply_to_all = cleaned_data.get('apply_to_all_classes')
        classes = cleaned_data.get('classes')
        is_exam = cleaned_data.get('is_exam_fee')
        exam_types = cleaned_data.get('exam_types')
        
        # Validation des classes
        if not apply_to_all and not classes:
            raise forms.ValidationError("Vous devez soit sélectionner des classes spécifiques, soit appliquer à toutes les classes.")
        
        # Validation des examens
        if is_exam and not exam_types:
            raise forms.ValidationError("Si c'est un frais d'examen, vous devez sélectionner au moins un type d'examen.")
        
        return cleaned_data

class ExtraFeePaymentForm(forms.ModelForm):
    """Formulaire pour le paiement des frais annexes"""
    
    # Champs de sélection
    extra_fee = forms.ModelChoiceField(
        queryset=ExtraFee.objects.none(),
        label="Frais annexe",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'onchange': 'updateClassSelection()'
        })
    )
    
    # Champ pour la classe (non stocké en base, juste pour la sélection)
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.none(),
        label="Classe",
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'onchange': 'updateStudentSelection()'
        })
    )
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),
        label="Étudiant",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'onchange': 'updateAmount()'
        })
    )
    
    # Montant (calculé automatiquement)
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Montant",
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'readonly': 'readonly',
            'id': 'id_amount'
        })
    )
    
    class Meta:
        model = ExtraFeePayment
        fields = ['extra_fee', 'student', 'amount', 'mode', 'notes']
        widgets = {
            'mode': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Notes additionnelles...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les frais annexes actifs et les classes
        try:
            current_year = CurrentSchoolYear.objects.first()
            if current_year:
                # Filtrer les frais annexes actifs de l'année actuelle
                self.fields['extra_fee'].queryset = ExtraFee.objects.filter(
                    year=current_year.year,
                    is_active=True
                ).select_related('fee_type')
                
                # Charger toutes les classes de l'année actuelle
                self.fields['school_class'].queryset = SchoolClass.objects.filter(year=current_year.year)
                
                # Charger tous les étudiants actifs de l'année actuelle
                self.fields['student'].queryset = Student.objects.filter(
                    current_class__year=current_year.year,
                    is_active=True
                ).select_related('current_class')
            else:
                # Si pas d'année actuelle, utiliser tous les frais
                self.fields['extra_fee'].queryset = ExtraFee.objects.filter(is_active=True)
                self.fields['school_class'].queryset = SchoolClass.objects.all()
                self.fields['student'].queryset = Student.objects.filter(is_active=True).select_related('current_class')
        except Exception as e:
            # En cas d'erreur, utiliser tous les frais
            self.fields['extra_fee'].queryset = ExtraFee.objects.filter(is_active=True)
            self.fields['school_class'].queryset = SchoolClass.objects.all()
            self.fields['student'].queryset = Student.objects.filter(is_active=True).select_related('current_class')
    
    def clean(self):
        cleaned_data = super().clean()
        # Pas de validation restrictive - permettre tous les paiements
        # La logique de filtrage se fait au niveau du frontend
        return cleaned_data

class BulkTranchePaymentForm(forms.Form):
    """Formulaire pour les paiements en lot"""
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        label="Classe",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tranche = forms.ModelChoiceField(
        queryset=FeeTranche.objects.all(),
        label="Tranche",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mode = forms.ChoiceField(
        choices=[('cash', 'Espèces'), ('cheque', 'Chèque'), ('mobile', 'Mobile Money'), ('virement', 'Virement')],
        label="Mode de paiement",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    receipt_prefix = forms.CharField(
        max_length=20,
        label="Préfixe des reçus",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )

class FeeStructureSearchForm(forms.Form):
    """Formulaire de recherche pour les structures de frais"""
    year = forms.ModelChoiceField(
        queryset=SchoolYear.objects.all(),
        label="Année scolaire",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        label="Classe",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class PaymentSearchForm(forms.Form):
    """Formulaire de recherche pour les paiements"""
    student_name = forms.CharField(
        max_length=100,
        label="Nom de l'étudiant",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rechercher par nom...'})
    )
    school_class = forms.ModelChoiceField(
        queryset=SchoolClass.objects.all(),
        label="Classe",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        label="Étudiant (sélection directe)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_type = forms.ChoiceField(
        choices=[
            ('', 'Tous les paiements'),
            ('inscription', 'Frais d\'inscription'),
            ('tranche', 'Tranches de scolarité')
        ],
        label="Type de paiement",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tranche = forms.ModelChoiceField(
        queryset=FeeTranche.objects.all(),
        label="Tranche",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mode = forms.ChoiceField(
        choices=[('', 'Tous')] + [('cash', 'Espèces'), ('cheque', 'Chèque'), ('mobile', 'Mobile Money'), ('virement', 'Virement')],
        label="Mode de paiement",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        label="Date de début",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        label="Date de fin",
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    ) 