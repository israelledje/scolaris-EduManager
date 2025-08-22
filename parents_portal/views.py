from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
import json
import logging

from .models import (
    ParentUser, ParentStudentRelation, ParentPaymentMethod,
    ParentPayment, ParentNotification, ParentLoginSession
)
from .forms import (
    ParentLoginForm, ParentRegistrationForm, ParentProfileForm,
    ParentPaymentMethodForm, PaymentForm, StudentSearchForm,
    NotificationFilterForm, FinancialFilterForm
)
from .services import ParentPortalService, PaymentService
from students.models import Student, Guardian, Attendance
from finances.models import (
    FeeTranche, TranchePayment, FeeStructure, InscriptionPayment,
    ExtraFee, ExtraFeePayment, FeeDiscount, Moratorium
)
from notes.models import Bulletin, Evaluation
from classes.models import SchoolClass
from school.models import SchoolYear

logger = logging.getLogger(__name__)

def parent_login(request):
    """Vue de connexion pour les parents"""
    if request.method == 'POST':
        form = ParentLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Rechercher l'utilisateur par username ou email
            try:
                if '@' in username_or_email:
                    parent_user = ParentUser.objects.get(email=username_or_email)
                else:
                    parent_user = ParentUser.objects.get(username=username_or_email)
                
                # Vérifier le mot de passe
                if parent_user.check_password(password) and parent_user.is_authenticated():
                    # Créer une session
                    session = ParentLoginSession.objects.create(
                        parent_user=parent_user,
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        login_time=timezone.now()
                    )
                    
                    # Stocker l'ID de session dans la session Django
                    request.session['parent_user_id'] = parent_user.id
                    request.session['parent_session_id'] = session.id
                    
                    # Gérer "Se souvenir de moi"
                    if not remember_me:
                        # Session courte si pas de "Se souvenir de moi"
                        request.session.set_expiry(3600)  # 1 heure
                    else:
                        # Session longue si "Se souvenir de moi" est coché
                        request.session.set_expiry(30 * 24 * 3600)  # 30 jours
                    
                    # Mettre à jour last_login
                    parent_user.last_login = timezone.now()
                    parent_user.save()
                    
                    messages.success(request, f"Bienvenue {parent_user.get_full_name()} !")
                    return redirect('parents_portal:dashboard')
                else:
                    messages.error(request, "Nom d'utilisateur/email ou mot de passe incorrect.")
            except ParentUser.DoesNotExist:
                messages.error(request, "Nom d'utilisateur/email ou mot de passe incorrect.")
            except Exception as e:
                logger.error(f"Erreur lors de la connexion: {str(e)}")
                messages.error(request, "Une erreur est survenue lors de la connexion. Veuillez réessayer.")
    else:
        form = ParentLoginForm()
    
    return render(request, 'parents_portal/login.html', {'form': form})

def parent_logout(request):
    """Vue de déconnexion pour les parents"""
    # Fermer la session parent
    session_id = request.session.get('parent_session_id')
    if session_id:
        try:
            session = ParentLoginSession.objects.get(id=session_id)
            session.logout_time = timezone.now()
            session.save()
        except ParentLoginSession.DoesNotExist:
            pass
    
    # Nettoyer la session Django
    request.session.pop('parent_user_id', None)
    request.session.pop('parent_session_id', None)
    
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('parents_portal:login')

def parent_register(request):
    """Vue d'inscription pour générer les comptes parents"""
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            guardian = form.cleaned_data['guardian_id']
            
            try:
                # Créer le compte parent
                parent_user = ParentPortalService.create_parent_account(guardian)
                messages.success(
                    request, 
                    f"Compte parent créé avec succès pour {guardian.name}. "
                    f"Les identifiants ont été envoyés à {guardian.email}"
                )
                return redirect('parents_portal:login')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du compte : {str(e)}")
    else:
        form = ParentRegistrationForm()
    
    return render(request, 'parents_portal/register.html', {'form': form})

def get_parent_user(request):
    """Fonction utilitaire pour récupérer l'utilisateur parent connecté"""
    parent_user_id = request.session.get('parent_user_id')
    if not parent_user_id:
        return None
    
    try:
        return ParentUser.objects.get(id=parent_user_id, is_active=True, status='ACTIVE')
    except ParentUser.DoesNotExist:
        return None

def parent_required(view_func):
    """Décorateur pour vérifier que l'utilisateur parent est connecté"""
    def wrapper(request, *args, **kwargs):
        parent_user = get_parent_user(request)
        if not parent_user:
            messages.error(request, "Veuillez vous connecter pour accéder à cette page.")
            return redirect('parents_portal:login')
        return view_func(request, *args, **kwargs)
    return wrapper

@parent_required
def parent_dashboard(request):
    """Tableau de bord principal des parents"""
    parent_user = get_parent_user(request)
    
    # Récupérer les étudiants via les profils de tuteur
    students = parent_user.get_students()
    
    # Récupérer les statistiques
    stats = ParentPortalService.get_parent_statistics(parent_user)
    
    # Récupérer les notifications récentes
    notifications = ParentPortalService.get_recent_notifications(parent_user, limit=5)
    
    # Récupérer les prochains paiements
    upcoming_payments = ParentPortalService.get_upcoming_payments(parent_user, limit=5)
    
    context = {
        'parent_user': parent_user,
        'students_count': len(students),
        'average_grade': stats.get('average_grade', 0),
        'pending_payments': stats.get('pending_payments', 0),
        'unread_notifications': stats.get('unread_notifications', 0),
        'students': students,
        'notifications': notifications,
        'upcoming_payments': upcoming_payments,
    }
    
    return render(request, 'parents_portal/dashboard.html', context)

@parent_required
def student_list(request):
    """Liste des étudiants du parent"""
    parent_user = get_parent_user(request)
    students = ParentPortalService.get_parent_students(parent_user)
    
    # Recherche et filtres
    search_form = StudentSearchForm(request.GET)
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search', '')
        if search_query:
            students = students.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(student_id__icontains=search_query)
            )
    
    # Pagination
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'parent_user': parent_user,
        'students': students,
        'page_obj': page_obj,
        'search_form': search_form,
    }
    
    return render(request, 'parents_portal/student_list.html', context)

@parent_required
def student_detail(request, student_id):
    """Détails d'un étudiant spécifique"""
    parent_user = get_parent_user(request)
    
    # Vérifier que l'étudiant appartient au parent
    try:
        relation = ParentStudentRelation.objects.get(
            parent_user=parent_user,
            student_id=student_id,
            is_active=True
        )
        student = relation.student
    except ParentStudentRelation.DoesNotExist:
        messages.error(request, "Vous n'avez pas accès à cet étudiant.")
        return redirect('parents_portal:student_list')
    
    # Récupérer les informations de l'étudiant
    academic_info = ParentPortalService.get_student_academic_info(student)
    financial_info = ParentPortalService.get_student_financial_info(student)
    attendance_info = ParentPortalService.get_student_attendance_info(student)
    
    context = {
        'parent_user': parent_user,
        'student': student,
        'relation': relation,
        'academic_info': academic_info,
        'financial_info': financial_info,
        'attendance_info': attendance_info,
    }
    
    return render(request, 'parents_portal/student_detail.html', context)

@parent_required
def get_student_grades(request, student_id):
    """Récupérer les notes d'un étudiant en AJAX"""
    parent_user = get_parent_user(request)
    
    # Vérifier l'accès
    try:
        relation = ParentStudentRelation.objects.get(
            parent_user=parent_user,
            student_id=student_id,
            is_active=True
        )
        student = relation.student
    except ParentStudentRelation.DoesNotExist:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    # Récupérer les notes
    grades = ParentPortalService.get_student_grades(student)
    
    return JsonResponse({'grades': grades})

@parent_required
def bulletin_view(request, bulletin_id):
    """Voir un bulletin spécifique"""
    parent_user = get_parent_user(request)
    
    try:
        bulletin = Bulletin.objects.get(id=bulletin_id)
        
        # Vérifier que l'étudiant du bulletin appartient au parent
        relation = ParentStudentRelation.objects.get(
            parent_user=parent_user,
            student=bulletin.student,
            is_active=True
        )
    except (Bulletin.DoesNotExist, ParentStudentRelation.DoesNotExist):
        messages.error(request, "Bulletin non trouvé ou accès non autorisé.")
        return redirect('parents_portal:dashboard')
    
    # Marquer la notification comme lue
    ParentNotification.objects.filter(
        parent_user=parent_user,
        notification_type='BULLETIN',
        related_id=bulletin_id
    ).update(is_read=True)
    
    context = {
        'parent_user': parent_user,
        'bulletin': bulletin,
        'student': bulletin.student,
    }
    
    return render(request, 'parents_portal/bulletin_view.html', context)

@parent_required
def financial_overview(request):
    """Vue d'ensemble financière mise à jour avec la nouvelle structure"""
    parent_user = get_parent_user(request)
    
    # Filtres
    filter_form = FinancialFilterForm(request.GET)
    students = ParentStudentRelation.objects.filter(
        parent_user=parent_user,
        is_active=True
    ).values_list('student_id', flat=True)
    
    # Récupérer l'année scolaire actuelle
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if not current_year:
        current_year = SchoolYear.objects.order_by('-annee').first()
    
    # Récupérer les informations financières détaillées
    financial_data = ParentPortalService.get_detailed_financial_overview(
        parent_user, current_year, request.GET
    )
    
    context = {
        'parent_user': parent_user,
        'filter_form': filter_form,
        'financial_data': financial_data,
        'current_year': current_year,
    }
    
    return render(request, 'parents_portal/financial_overview.html', context)

@parent_required
def student_financial_detail(request, student_id):
    """Vue détaillée des finances d'un étudiant spécifique"""
    parent_user = get_parent_user(request)
    
    # Vérifier l'accès à l'étudiant
    try:
        relation = ParentStudentRelation.objects.get(
            parent_user=parent_user,
            student_id=student_id,
            is_active=True
        )
        student = relation.student
    except ParentStudentRelation.DoesNotExist:
        messages.error(request, "Accès non autorisé à cet étudiant.")
        return redirect('parents_portal:financial_overview')
    
    # Récupérer l'année scolaire actuelle
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if not current_year:
        current_year = SchoolYear.objects.order_by('-annee').first()
    
    # Récupérer les informations financières détaillées de l'étudiant
    student_financial_data = ParentPortalService.get_student_detailed_financial_info(
        student, current_year
    )
    
    context = {
        'parent_user': parent_user,
        'student': student,
        'relation': relation,
        'financial_data': student_financial_data,
        'current_year': current_year,
    }
    
    return render(request, 'parents_portal/student_financial_detail.html', context)

@parent_required
def make_tranche_payment(request, student_id, tranche_id):
    """Effectuer un paiement de tranche"""
    parent_user = get_parent_user(request)
    
    # Vérifier l'accès à l'étudiant
    try:
        relation = ParentStudentRelation.objects.get(
            parent_user=parent_user,
            student_id=student_id,
            is_active=True
        )
        student = relation.student
    except ParentStudentRelation.DoesNotExist:
        messages.error(request, "Accès non autorisé à cet étudiant.")
        return redirect('parents_portal:financial_overview')
    
    # Récupérer la tranche
    try:
        tranche = FeeTranche.objects.get(id=tranche_id)
    except FeeTranche.DoesNotExist:
        messages.error(request, "Tranche de frais non trouvée.")
        return redirect('parents_portal:financial_overview')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, parent_user=parent_user)
        if form.is_valid():
            try:
                payment = PaymentService.create_tranche_payment(
                    parent_user=parent_user,
                    student=student,
                    tranche=tranche,
                    payment_method=form.cleaned_data['payment_method'],
                    amount=form.cleaned_data['amount']
                )
                
                messages.success(request, "Paiement initié avec succès !")
                return redirect('parents_portal:payment_success', payment_id=payment.id)
            except Exception as e:
                messages.error(request, f"Erreur lors du paiement : {str(e)}")
    else:
        form = PaymentForm(parent_user=parent_user)
    
    context = {
        'parent_user': parent_user,
        'student': student,
        'tranche': tranche,
        'form': form,
    }
    
    return render(request, 'parents_portal/make_tranche_payment.html', context)

@parent_required
def make_inscription_payment(request, student_id):
    """Effectuer un paiement des frais d'inscription"""
    parent_user = get_parent_user(request)
    
    # Vérifier l'accès à l'étudiant
    try:
        relation = ParentStudentRelation.objects.get(
            parent_user=parent_user,
            student_id=student_id,
            is_active=True
        )
        student = relation.student
    except ParentStudentRelation.DoesNotExist:
        messages.error(request, "Accès non autorisé à cet étudiant.")
        return redirect('parents_portal:financial_overview')
    
    # Récupérer la structure des frais d'inscription
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if not current_year:
        current_year = SchoolYear.objects.order_by('-annee').first()
    
    try:
        fee_structure = FeeStructure.objects.get(
            school_class=student.current_class,
            year=current_year
        )
    except FeeStructure.DoesNotExist:
        messages.error(request, "Structure des frais non trouvée pour cet étudiant.")
        return redirect('parents_portal:financial_overview')
    
    # Vérifier si l'inscription est déjà payée
    existing_payment = InscriptionPayment.objects.filter(
        student=student,
        fee_structure=fee_structure
    ).first()
    
    if existing_payment:
        messages.info(request, "Les frais d'inscription sont déjà payés pour cet étudiant.")
        return redirect('parents_portal:student_financial_detail', student_id=student_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, parent_user=parent_user)
        if form.is_valid():
            try:
                payment = PaymentService.create_inscription_payment(
                    parent_user=parent_user,
                    student=student,
                    fee_structure=fee_structure,
                    payment_method=form.cleaned_data['payment_method'],
                    amount=form.cleaned_data['amount']
                )
                
                messages.success(request, "Paiement des frais d'inscription initié avec succès !")
                return redirect('parents_portal:payment_success', payment_id=payment.id)
            except Exception as e:
                messages.error(request, f"Erreur lors du paiement : {str(e)}")
    else:
        form = PaymentForm(parent_user=parent_user)
    
    context = {
        'parent_user': parent_user,
        'student': student,
        'fee_structure': fee_structure,
        'form': form,
    }
    
    return render(request, 'parents_portal/make_inscription_payment.html', context)

@parent_required
def make_extra_fee_payment(request, student_id, extra_fee_id):
    """Effectuer un paiement de frais annexe"""
    parent_user = get_parent_user(request)
    
    # Vérifier l'accès à l'étudiant
    try:
        relation = ParentStudentRelation.objects.get(
            parent_user=parent_user,
            student_id=student_id,
            is_active=True
        )
        student = relation.student
    except ParentStudentRelation.DoesNotExist:
        messages.error(request, "Accès non autorisé à cet étudiant.")
        return redirect('parents_portal:financial_overview')
    
    # Récupérer le frais annexe
    try:
        extra_fee = ExtraFee.objects.get(id=extra_fee_id)
    except ExtraFee.DoesNotExist:
        messages.error(request, "Frais annexe non trouvé.")
        return redirect('parents_portal:financial_overview')
    
    # Vérifier si le frais annexe est déjà payé
    existing_payment = ExtraFeePayment.objects.filter(
        student=student,
        extra_fee=extra_fee
    ).first()
    
    if existing_payment:
        messages.info(request, "Ce frais annexe est déjà payé pour cet étudiant.")
        return redirect('parents_portal:student_financial_detail', student_id=student_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, parent_user=parent_user)
        if form.is_valid():
            try:
                payment = PaymentService.create_extra_fee_payment(
                    parent_user=parent_user,
                    student=student,
                    extra_fee=extra_fee,
                    payment_method=form.cleaned_data['payment_method'],
                    amount=form.cleaned_data['amount']
                )
                
                messages.success(request, "Paiement du frais annexe initié avec succès !")
                return redirect('parents_portal:payment_success', payment_id=payment.id)
            except Exception as e:
                messages.error(request, f"Erreur lors du paiement : {str(e)}")
    else:
        form = PaymentForm(parent_user=parent_user)
    
    context = {
        'parent_user': parent_user,
        'student': student,
        'extra_fee': extra_fee,
        'form': form,
    }
    
    return render(request, 'parents_portal/make_extra_fee_payment.html', context)

@parent_required
def payment_receipt(request, payment_id):
    """Afficher le reçu de paiement"""
    parent_user = get_parent_user(request)
    
    try:
        payment = ParentPayment.objects.get(
            id=payment_id,
            parent_user=parent_user
        )
    except ParentPayment.DoesNotExist:
        messages.error(request, "Paiement non trouvé.")
        return redirect('parents_portal:financial_overview')
    
    context = {
        'parent_user': parent_user,
        'payment': payment,
    }
    
    return render(request, 'parents_portal/payment_receipt.html', context)

@parent_required
def financial_reports(request):
    """Rapports financiers détaillés"""
    parent_user = get_parent_user(request)
    
    # Filtres pour les rapports
    year_filter = request.GET.get('year')
    student_filter = request.GET.get('student')
    
    # Récupérer les années disponibles
    available_years = SchoolYear.objects.all().order_by('-annee')
    
    # Récupérer l'année sélectionnée
    selected_year = None
    if year_filter:
        try:
            selected_year = SchoolYear.objects.get(id=year_filter)
        except SchoolYear.DoesNotExist:
            pass
    
    if not selected_year:
        selected_year = SchoolYear.objects.filter(is_active=True).first()
        if not selected_year:
            selected_year = available_years.first()
    
    # Récupérer les rapports financiers
    financial_reports = ParentPortalService.get_financial_reports(
        parent_user, selected_year, student_filter
    )
    
    context = {
        'parent_user': parent_user,
        'financial_reports': financial_reports,
        'available_years': available_years,
        'selected_year': selected_year,
        'student_filter': student_filter,
    }
    
    return render(request, 'parents_portal/financial_reports.html', context)

@parent_required
def parent_profile(request):
    """Profil du parent"""
    parent_user = get_parent_user(request)
    
    if request.method == 'POST':
        form = ParentProfileForm(request.POST, instance=parent_user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('parents_portal:profile')
    else:
        form = ParentProfileForm(instance=parent_user)
    
    # Récupérer les méthodes de paiement
    payment_methods = ParentPaymentMethod.objects.filter(parent_user=parent_user)
    
    context = {
        'parent_user': parent_user,
        'form': form,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'parents_portal/profile.html', context)

@parent_required
def add_payment_method(request):
    """Ajouter une méthode de paiement"""
    parent_user = get_parent_user(request)
    
    if request.method == 'POST':
        form = ParentPaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save(commit=False)
            payment_method.parent_user = parent_user
            payment_method.save()
            
            messages.success(request, "Méthode de paiement ajoutée avec succès !")
            return redirect('parents_portal:profile')
    else:
        form = ParentPaymentMethodForm()
    
    context = {
        'parent_user': parent_user,
        'form': form,
    }
    
    return render(request, 'parents_portal/add_payment_method.html', context)

@parent_required
def remove_payment_method(request, method_id):
    """Supprimer une méthode de paiement"""
    parent_user = get_parent_user(request)
    
    try:
        payment_method = ParentPaymentMethod.objects.get(
            id=method_id,
            parent_user=parent_user
        )
        payment_method.delete()
        messages.success(request, "Méthode de paiement supprimée avec succès !")
    except ParentPaymentMethod.DoesNotExist:
        messages.error(request, "Méthode de paiement non trouvée.")
    
    return redirect('parents_portal:profile')

@parent_required
def notifications(request):
    """Centre de notifications"""
    parent_user = get_parent_user(request)
    
    # Filtres
    filter_form = NotificationFilterForm(request.GET)
    notifications = ParentNotification.objects.filter(parent_user=parent_user)
    
    # Appliquer les filtres
    if filter_form.is_valid():
        notification_type = filter_form.cleaned_data.get('notification_type')
        is_read = filter_form.cleaned_data.get('is_read')
        search = filter_form.cleaned_data.get('search')
        
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        if is_read is not None:
            notifications = notifications.filter(is_read=is_read)
        if search:
            notifications = notifications.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )
    
    # Pagination
    paginator = Paginator(notifications.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'parent_user': parent_user,
        'notifications': notifications,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'unread_count': ParentNotification.objects.filter(
            parent_user=parent_user, is_read=False
        ).count(),
        'total_count': notifications.count(),
    }
    
    return render(request, 'parents_portal/notifications.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request):
    """Webhook pour les notifications de paiement"""
    try:
        data = json.loads(request.body)
        
        # Traiter la notification de paiement
        payment_status = PaymentService.process_payment_webhook(data)
        
        return JsonResponse({'status': 'success', 'payment_status': payment_status})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Erreur webhook paiement: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@parent_required
def payment_success(request, payment_id):
    """Page de succès après un paiement"""
    parent_user = get_parent_user(request)
    
    try:
        payment = ParentPayment.objects.get(
            id=payment_id,
            parent_user=parent_user
        )
    except ParentPayment.DoesNotExist:
        messages.error(request, "Paiement non trouvé.")
        return redirect('parents_portal:financial_overview')
    
    context = {
        'parent_user': parent_user,
        'payment': payment,
    }
    
    return render(request, 'parents_portal/payment_success.html', context)


@parent_required
def payment_history(request):
    """Historique des paiements"""
    parent_user = get_parent_user(request)
    
    # Récupérer l'année scolaire actuelle
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if not current_year:
        current_year = SchoolYear.objects.order_by('-annee').first()
    
    # Récupérer l'historique des paiements
    payment_history = ParentPortalService.get_payment_history(parent_user, current_year)
    
    # Pagination
    paginator = Paginator(payment_history, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'parent_user': parent_user,
        'payment_history': payment_history,
        'page_obj': page_obj,
        'current_year': current_year,
    }
    
    return render(request, 'parents_portal/payment_history.html', context)
