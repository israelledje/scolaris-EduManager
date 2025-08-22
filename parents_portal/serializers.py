from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import (
    ParentUser, ParentStudentRelation, ParentPaymentMethod,
    ParentPayment, ParentNotification, ParentLoginSession
)
from students.models import Student, Guardian
from finances.models import (
    FeeTranche, TranchePayment, FeeStructure, InscriptionPayment,
    ExtraFee, ExtraFeePayment, FeeDiscount, Moratorium
)
from notes.models import Bulletin, Evaluation
from classes.models import SchoolClass
from school.models import SchoolYear


# ==================== SERIALIZERS D'AUTHENTIFICATION ====================

class ParentLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion des parents"""
    username_or_email = serializers.CharField(
        label="Nom d'utilisateur ou email",
        help_text="Entrez votre nom d'utilisateur ou votre adresse email"
    )
    password = serializers.CharField(
        label="Mot de passe",
        style={'input_type': 'password'},
        help_text="Entrez votre mot de passe"
    )
    remember_me = serializers.BooleanField(
        required=False,
        default=False,
        label="Se souvenir de moi"
    )

    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')

        if username_or_email and password:
            # Rechercher l'utilisateur par username ou email
            try:
                if '@' in username_or_email:
                    parent_user = ParentUser.objects.get(email=username_or_email)
                else:
                    parent_user = ParentUser.objects.get(username=username_or_email)
                
                # Vérifier le mot de passe
                if not parent_user.check_password(password):
                    raise serializers.ValidationError(
                        "Nom d'utilisateur/email ou mot de passe incorrect."
                    )
                
                if not parent_user.is_authenticated():
                    raise serializers.ValidationError(
                        "Votre compte est désactivé ou suspendu."
                    )
                
                attrs['parent_user'] = parent_user
                return attrs
                
            except ParentUser.DoesNotExist:
                raise serializers.ValidationError(
                    "Nom d'utilisateur/email ou mot de passe incorrect."
                )
        else:
            raise serializers.ValidationError(
                "Veuillez fournir un nom d'utilisateur/email et un mot de passe."
            )


class ParentRegistrationSerializer(serializers.Serializer):
    """Serializer pour l'inscription des parents"""
    guardian_id = serializers.IntegerField(
        label="ID du tuteur",
        help_text="Sélectionnez le tuteur pour lequel créer le compte"
    )

    def validate_guardian_id(self, value):
        try:
            guardian = Guardian.objects.get(id=value)
            # Vérifier que le guardian n'a pas déjà un compte
            if ParentUser.objects.filter(email=guardian.email).exists():
                raise serializers.ValidationError(
                    "Ce tuteur a déjà un compte dans le portail."
                )
            return value
        except Guardian.DoesNotExist:
            raise serializers.ValidationError(
                "Tuteur non trouvé."
            )


# ==================== SERIALIZERS DES MODÈLES PRINCIPAUX ====================

class ParentUserSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ParentUser"""
    full_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = ParentUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'role_display', 'status', 'status_display',
            'is_active', 'last_login', 'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def validate_email(self, value):
        if ParentUser.objects.exclude(pk=self.instance.pk if self.instance else None).filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse email est déjà utilisée.")
        return value
    
    def validate_username(self, value):
        if ParentUser.objects.exclude(pk=self.instance.pk if self.instance else None).filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value


class ParentUserCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un ParentUser"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = ParentUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone',
            'role', 'password', 'confirm_password'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        parent_user = ParentUser.objects.create(**validated_data)
        parent_user.set_password(password)
        parent_user.save()
        return parent_user


class ParentUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'un ParentUser"""
    class Meta:
        model = ParentUser
        fields = ['first_name', 'last_name', 'phone', 'email']
    
    def validate_email(self, value):
        if ParentUser.objects.exclude(pk=self.instance.pk).filter(email=value).exists():
            raise serializers.ValidationError("Cette adresse email est déjà utilisée.")
        return value


class ParentStudentRelationSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ParentStudentRelation"""
    parent_user = ParentUserSerializer(read_only=True)
    student = serializers.SerializerMethodField()
    relation_type_display = serializers.CharField(source='get_relation_type_display', read_only=True)
    
    class Meta:
        model = ParentStudentRelation
        fields = [
            'id', 'parent_user', 'student', 'relation_type', 'relation_type_display',
            'is_active', 'can_view_academic', 'can_view_financial',
            'can_make_payments', 'can_view_attendance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student(self, obj):
        return {
            'id': obj.student.id,
            'first_name': obj.student.first_name,
            'last_name': obj.student.last_name,
            'matricule': obj.student.matricule,
            'current_class': obj.student.current_class.name if obj.student.current_class else None
        }


class ParentPaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ParentPaymentMethod"""
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    
    class Meta:
        model = ParentPaymentMethod
        fields = [
            'id', 'method_type', 'method_type_display', 'account_number',
            'account_name', 'is_default', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        if attrs.get('is_default'):
            # Désactiver les autres méthodes par défaut
            ParentPaymentMethod.objects.filter(
                parent_user=self.context['request'].user,
                is_default=True
            ).update(is_default=False)
        return attrs


class ParentPaymentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ParentPayment"""
    parent_user = ParentUserSerializer(read_only=True)
    student = serializers.SerializerMethodField()
    tranche = serializers.SerializerMethodField()
    payment_method = ParentPaymentMethodSerializer(read_only=True)
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ParentPayment
        fields = [
            'id', 'payment_id', 'parent_user', 'student', 'tranche',
            'amount', 'fees', 'total_amount', 'payment_method', 'method_type',
            'method_type_display', 'status', 'status_display', 'transaction_id',
            'receipt_url', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'payment_id', 'parent_user', 'created_at', 'updated_at'
        ]
    
    def get_student(self, obj):
        return {
            'id': obj.student.id,
            'first_name': obj.student.first_name,
            'last_name': obj.student.last_name,
            'matricule': obj.student.matricule
        }
    
    def get_tranche(self, obj):
        if obj.tranche:
            return {
                'id': obj.tranche.id,
                'number': obj.tranche.number,
                'amount': obj.tranche.amount,
                'due_date': obj.tranche.due_date
            }
        return None


class ParentNotificationSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ParentNotification"""
    parent_user = ParentUserSerializer(read_only=True)
    related_student = serializers.SerializerMethodField()
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = ParentNotification
        fields = [
            'id', 'parent_user', 'notification_type', 'notification_type_display',
            'title', 'message', 'related_student', 'related_url', 'is_read',
            'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'parent_user', 'created_at']
    
    def get_related_student(self, obj):
        if obj.related_student:
            return {
                'id': obj.related_student.id,
                'first_name': obj.related_student.first_name,
                'last_name': obj.related_student.last_name,
                'matricule': obj.related_student.matricule
            }
        return None


class ParentLoginSessionSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ParentLoginSession"""
    parent_user = ParentUserSerializer(read_only=True)
    
    class Meta:
        model = ParentLoginSession
        fields = [
            'id', 'parent_user', 'ip_address', 'user_agent', 'login_time',
            'logout_time', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ==================== SERIALIZERS DES ÉTUDIANTS ET FINANCES ====================

class StudentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Student"""
    current_class = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'matricule', 'first_name', 'last_name', 'birth_date',
            'birth_place', 'gender', 'gender_display', 'nationality',
            'address', 'phone', 'current_class', 'enrollment_date',
            'photo', 'year', 'school', 'is_active', 'is_repeating',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_current_class(self, obj):
        if obj.current_class:
            return {
                'id': obj.current_class.id,
                'name': obj.current_class.name,
                'level': obj.current_class.level
            }
        return None


class FeeStructureSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle FeeStructure"""
    school_class = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    
    class Meta:
        model = FeeStructure
        fields = [
            'id', 'school_class', 'year', 'inscription_fee', 'tuition_total',
            'tranche_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_school_class(self, obj):
        return {
            'id': obj.school_class.id,
            'name': obj.school_class.name,
            'level': obj.school_class.level
        }
    
    def get_year(self, obj):
        return {
            'id': obj.year.id,
            'annee': obj.year.annee,
            'is_active': obj.year.is_active
        }


class FeeTrancheSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle FeeTranche"""
    fee_structure = FeeStructureSerializer(read_only=True)
    
    class Meta:
        model = FeeTranche
        fields = [
            'id', 'fee_structure', 'number', 'amount', 'due_date'
        ]
        read_only_fields = ['id']


class TranchePaymentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle TranchePayment"""
    student = StudentSerializer(read_only=True)
    tranche = FeeTrancheSerializer(read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    
    class Meta:
        model = TranchePayment
        fields = [
            'id', 'student', 'tranche', 'amount', 'payment_date',
            'mode', 'mode_display', 'receipt', 'document', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InscriptionPaymentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle InscriptionPayment"""
    student = StudentSerializer(read_only=True)
    fee_structure = FeeStructureSerializer(read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    
    class Meta:
        model = InscriptionPayment
        fields = [
            'id', 'student', 'fee_structure', 'amount', 'payment_date',
            'mode', 'mode_display', 'receipt', 'document', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ExtraFeeSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ExtraFee"""
    fee_type = serializers.SerializerMethodField()
    classes = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    
    class Meta:
        model = ExtraFee
        fields = [
            'id', 'name', 'fee_type', 'is_exam_fee', 'exam_types',
            'apply_to_all_classes', 'classes', 'amount', 'amounts_by_class',
            'year', 'due_date', 'is_optional', 'is_active', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_fee_type(self, obj):
        if obj.fee_type:
            return {
                'id': obj.fee_type.id,
                'name': obj.fee_type.name,
                'description': obj.fee_type.description
            }
        return None
    
    def get_classes(self, obj):
        return [
            {
                'id': cls.id,
                'name': cls.name,
                'level': cls.level
            }
            for cls in obj.classes.all()
        ]
    
    def get_year(self, obj):
        return {
            'id': obj.year.id,
            'annee': obj.year.annee,
            'is_active': obj.year.is_active
        }


class ExtraFeePaymentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ExtraFeePayment"""
    student = StudentSerializer(read_only=True)
    extra_fee = ExtraFeeSerializer(read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    
    class Meta:
        model = ExtraFeePayment
        fields = [
            'id', 'student', 'extra_fee', 'amount', 'payment_date',
            'mode', 'mode_display', 'receipt', 'document', 'notes',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FeeDiscountSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle FeeDiscount"""
    student = StudentSerializer(read_only=True)
    tranche = FeeTrancheSerializer(read_only=True)
    
    class Meta:
        model = FeeDiscount
        fields = [
            'id', 'student', 'tranche', 'amount', 'reason',
            'granted_at', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MoratoriumSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Moratorium"""
    student = StudentSerializer(read_only=True)
    tranche = FeeTrancheSerializer(read_only=True)
    
    class Meta:
        model = Moratorium
        fields = [
            'id', 'student', 'tranche', 'amount', 'new_due_date',
            'reason', 'is_approved', 'requested_at', 'approved_at'
        ]
        read_only_fields = ['id', 'requested_at']


# ==================== SERIALIZERS POUR LES VUES FINANCIÈRES ====================

class StudentFinancialSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé financier d'un étudiant"""
    student = StudentSerializer()
    total_inscription_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_inscription_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tuition_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tuition_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_extra_fees_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_extra_fees_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_discounts = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_remaining = serializers.DecimalField(max_digits=10, decimal_places=2)


class TrancheStatusSerializer(serializers.Serializer):
    """Serializer pour le statut d'une tranche"""
    tranche = FeeTrancheSerializer()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    discounts = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()
    due_date = serializers.DateField()
    days_until_due = serializers.IntegerField()


class ExtraFeeStatusSerializer(serializers.Serializer):
    """Serializer pour le statut d'un frais annexe"""
    extra_fee = ExtraFeeSerializer()
    amount_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment = ExtraFeePaymentSerializer()
    status = serializers.CharField()
    due_date = serializers.DateField(allow_null=True)


class PaymentHistoryItemSerializer(serializers.Serializer):
    """Serializer pour un élément de l'historique des paiements"""
    type = serializers.CharField()
    payment = serializers.DictField()
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    date = serializers.DateField()
    mode = serializers.CharField()


class StudentDetailedFinancialSerializer(serializers.Serializer):
    """Serializer pour les informations financières détaillées d'un étudiant"""
    financial_summary = StudentFinancialSummarySerializer()
    tranches_status = TrancheStatusSerializer(many=True)
    extra_fees_status = ExtraFeeStatusSerializer(many=True)
    payment_history = PaymentHistoryItemSerializer(many=True)


class FinancialOverviewSerializer(serializers.Serializer):
    """Serializer pour la vue d'ensemble financière"""
    students = StudentDetailedFinancialSerializer(many=True)
    total_inscription_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_inscription_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tuition_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tuition_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_extra_fees_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_extra_fees_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_due = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_discounts = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_remaining = serializers.DecimalField(max_digits=10, decimal_places=2)


# ==================== SERIALIZERS POUR LES FORMULAIRES ====================

class PaymentFormSerializer(serializers.Serializer):
    """Serializer pour le formulaire de paiement"""
    payment_method = serializers.PrimaryKeyRelatedField(
        queryset=ParentPaymentMethod.objects.all(),
        label="Méthode de paiement"
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Montant",
        min_value=0.01
    )


class StudentSearchSerializer(serializers.Serializer):
    """Serializer pour la recherche d'étudiants"""
    search = serializers.CharField(
        required=False,
        allow_blank=True,
        label="Recherche",
        help_text="Rechercher par nom, prénom ou matricule"
    )


class FinancialFilterSerializer(serializers.Serializer):
    """Serializer pour les filtres financiers"""
    year = serializers.PrimaryKeyRelatedField(
        queryset=SchoolYear.objects.all(),
        required=False,
        allow_null=True,
        label="Année scolaire"
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        required=False,
        allow_null=True,
        label="Étudiant"
    )
    status = serializers.ChoiceField(
        choices=[
            ('PAID', 'Payé'),
            ('PARTIAL', 'Partiel'),
            ('PENDING', 'En attente'),
            ('OVERDUE', 'En retard')
        ],
        required=False,
        allow_blank=True,
        label="Statut"
    )


class NotificationFilterSerializer(serializers.Serializer):
    """Serializer pour les filtres de notifications"""
    notification_type = serializers.ChoiceField(
        choices=ParentNotification.NOTIFICATION_TYPE_CHOICES,
        required=False,
        allow_blank=True,
        label="Type de notification"
    )
    is_read = serializers.BooleanField(
        required=False,
        allow_null=True,
        label="Lu"
    )
    search = serializers.CharField(
        required=False,
        allow_blank=True,
        label="Recherche",
        help_text="Rechercher dans le titre ou le message"
    )


# ==================== SERIALIZERS POUR LES RÉPONSES API ====================

class APIResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses API standardisées"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.DictField(required=False, allow_null=True)
    errors = serializers.ListField(required=False, allow_null=True)


class PaginatedResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses paginées"""
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = serializers.ListField()


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'erreur"""
    error = serializers.CharField()
    detail = serializers.CharField(required=False, allow_blank=True)
    code = serializers.CharField(required=False, allow_blank=True)
