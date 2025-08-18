from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import migrations

def create_finance_permissions(apps, schema_editor):
    """Créer les permissions personnalisées pour l'app finances"""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    
    # Récupérer le content type pour l'app finances
    try:
        finance_ct = ContentType.objects.get(app_label='finances')
    except ContentType.DoesNotExist:
        return
    
    # Permissions pour les structures de frais
    Permission.objects.get_or_create(
        codename='view_fee_structure',
        name='Peut voir les structures de frais',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='add_fee_structure',
        name='Peut ajouter des structures de frais',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='change_fee_structure',
        name='Peut modifier les structures de frais',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='delete_fee_structure',
        name='Peut supprimer les structures de frais',
        content_type=finance_ct,
    )
    
    # Permissions pour les paiements
    Permission.objects.get_or_create(
        codename='view_tranchepayment',
        name='Peut voir les paiements',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='add_tranchepayment',
        name='Peut ajouter des paiements',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='change_tranchepayment',
        name='Peut modifier les paiements',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='delete_tranchepayment',
        name='Peut supprimer les paiements',
        content_type=finance_ct,
    )
    
    # Permissions pour les remises
    Permission.objects.get_or_create(
        codename='view_feediscount',
        name='Peut voir les remises',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='add_feediscount',
        name='Peut ajouter des remises',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='change_feediscount',
        name='Peut modifier les remises',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='delete_feediscount',
        name='Peut supprimer les remises',
        content_type=finance_ct,
    )
    
    # Permissions pour les moratoires
    Permission.objects.get_or_create(
        codename='view_moratorium',
        name='Peut voir les moratoires',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='add_moratorium',
        name='Peut ajouter des moratoires',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='change_moratorium',
        name='Peut modifier les moratoires',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='delete_moratorium',
        name='Peut supprimer les moratoires',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='approve_moratorium',
        name='Peut approuver les moratoires',
        content_type=finance_ct,
    )
    
    # Permissions pour les remboursements
    Permission.objects.get_or_create(
        codename='view_paymentrefund',
        name='Peut voir les remboursements',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='add_paymentrefund',
        name='Peut ajouter des remboursements',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='change_paymentrefund',
        name='Peut modifier les remboursements',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='delete_paymentrefund',
        name='Peut supprimer les remboursements',
        content_type=finance_ct,
    )
    
    # Permissions pour les frais annexes
    Permission.objects.get_or_create(
        codename='view_extrafee',
        name='Peut voir les frais annexes',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='add_extrafee',
        name='Peut ajouter des frais annexes',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='change_extrafee',
        name='Peut modifier les frais annexes',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='delete_extrafee',
        name='Peut supprimer les frais annexes',
        content_type=finance_ct,
    )
    
    # Permissions spéciales
    Permission.objects.get_or_create(
        codename='view_financial_dashboard',
        name='Peut voir le tableau de bord financier',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='print_receipts',
        name='Peut imprimer les reçus',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='view_financial_reports',
        name='Peut voir les rapports financiers',
        content_type=finance_ct,
    )
    Permission.objects.get_or_create(
        codename='bulk_payments',
        name='Peut effectuer des paiements en lot',
        content_type=finance_ct,
    )

def remove_finance_permissions(apps, schema_editor):
    """Supprimer les permissions personnalisées pour l'app finances"""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    
    try:
        finance_ct = ContentType.objects.get(app_label='finances')
        Permission.objects.filter(content_type=finance_ct).delete()
    except ContentType.DoesNotExist:
        pass

class Migration(migrations.Migration):
    dependencies = [
        ('finances', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(create_finance_permissions, remove_finance_permissions),
    ]

# Définition des groupes de permissions par rôle
FINANCE_PERMISSIONS_BY_ROLE = {
    'ADMIN': [
        'finances.view_financial_dashboard',
        'finances.view_fee_structure',
        'finances.add_fee_structure',
        'finances.change_fee_structure',
        'finances.delete_fee_structure',
        'finances.view_tranchepayment',
        'finances.add_tranchepayment',
        'finances.change_tranchepayment',
        'finances.delete_tranchepayment',
        'finances.view_feediscount',
        'finances.add_feediscount',
        'finances.change_feediscount',
        'finances.delete_feediscount',
        'finances.view_moratorium',
        'finances.add_moratorium',
        'finances.change_moratorium',
        'finances.delete_moratorium',
        'finances.approve_moratorium',
        'finances.view_paymentrefund',
        'finances.add_paymentrefund',
        'finances.change_paymentrefund',
        'finances.delete_paymentrefund',
        'finances.view_extrafee',
        'finances.add_extrafee',
        'finances.change_extrafee',
        'finances.delete_extrafee',
        'finances.print_receipts',
        'finances.view_financial_reports',
        'finances.bulk_payments',
    ],
    'DIRECTION': [
        'finances.view_financial_dashboard',
        'finances.view_fee_structure',
        'finances.add_fee_structure',
        'finances.change_fee_structure',
        'finances.view_tranchepayment',
        'finances.add_tranchepayment',
        'finances.change_tranchepayment',
        'finances.view_feediscount',
        'finances.add_feediscount',
        'finances.change_feediscount',
        'finances.view_moratorium',
        'finances.add_moratorium',
        'finances.change_moratorium',
        'finances.approve_moratorium',
        'finances.view_paymentrefund',
        'finances.add_paymentrefund',
        'finances.view_extrafee',
        'finances.add_extrafee',
        'finances.change_extrafee',
        'finances.print_receipts',
        'finances.view_financial_reports',
        'finances.bulk_payments',
    ],
    'SURVEILLANCE': [
        'finances.view_financial_dashboard',
        'finances.view_fee_structure',
        'finances.view_tranchepayment',
        'finances.add_tranchepayment',
        'finances.view_feediscount',
        'finances.view_moratorium',
        'finances.add_moratorium',
        'finances.view_extrafee',
        'finances.print_receipts',
    ],
    'PROFESSEUR': [
        'finances.view_financial_dashboard',
        'finances.view_fee_structure',
        'finances.view_tranchepayment',
        'finances.view_feediscount',
        'finances.view_moratorium',
        'finances.view_extrafee',
    ],
    'PARENT': [
        'finances.view_financial_dashboard',
        'finances.view_tranchepayment',
        'finances.view_feediscount',
        'finances.view_moratorium',
        'finances.add_moratorium',
        'finances.view_extrafee',
    ],
    'ELEVE': [
        'finances.view_financial_dashboard',
        'finances.view_tranchepayment',
        'finances.view_feediscount',
        'finances.view_moratorium',
        'finances.view_extrafee',
    ],
}

def get_finance_permissions_for_role(role):
    """Récupérer les permissions financières pour un rôle donné"""
    return FINANCE_PERMISSIONS_BY_ROLE.get(role, [])

def assign_finance_permissions_to_user(user, role):
    """Assigner les permissions financières à un utilisateur selon son rôle"""
    from django.contrib.auth.models import Permission
    
    # Récupérer les permissions pour le rôle
    permission_codenames = get_finance_permissions_for_role(role)
    
    # Récupérer les objets Permission
    permissions = Permission.objects.filter(
        codename__in=[perm.split('.')[-1] for perm in permission_codenames],
        content_type__app_label='finances'
    )
    
    # Assigner les permissions à l'utilisateur
    user.user_permissions.add(*permissions)
    
    return permissions

def check_finance_permission(user, permission_name):
    """Vérifier si un utilisateur a une permission financière spécifique"""
    return user.has_perm(f'finances.{permission_name}')

# Décorateurs de permissions personnalisés
from functools import wraps
from django.core.exceptions import PermissionDenied

def require_finance_permission(permission_name):
    """Décorateur pour vérifier une permission financière"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not check_finance_permission(request.user, permission_name):
                raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_finance_role(allowed_roles):
    """Décorateur pour vérifier le rôle de l'utilisateur"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied("Vous n'avez pas le rôle requis pour accéder à cette page.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 