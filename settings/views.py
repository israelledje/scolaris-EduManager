from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from school.models import MatriculeSequence, SchoolYear
from school.services import MatriculeService
from authentication.models import User
from authentication.mixins import admin_or_direction_required
from teachers.models import Teacher
from django.views.decorators.http import require_http_methods
import json
import string
import secrets
from datetime import datetime

@login_required
def matricule_settings(request):
    """Vue pour gérer les paramètres des matricules"""
    
    # Traitement du formulaire POST
    if request.method == 'POST':
        sequence_type = request.POST.get('sequence_type')
        prefix = request.POST.get('prefix')
        format_pattern = request.POST.get('format_pattern')
        auto_generation = request.POST.get('auto_generation') == 'on'
        
        if sequence_type and prefix and format_pattern:
            # Récupérer l'année courante
            current_year_obj = SchoolYear.objects.filter(statut='EN_COURS').first()
            if current_year_obj:
                # Extraire l'année de début depuis le format "2024-2025"
                current_year = int(current_year_obj.annee.split('-')[0])
                
                # Créer ou mettre à jour la séquence
                sequence, created = MatriculeSequence.objects.get_or_create(
                    sequence_type=sequence_type,
                    defaults={
                        'prefix': prefix,
                        'format_pattern': format_pattern,
                        'current_year': current_year,
                        'auto_generation': auto_generation,
                        'last_number': 0
                    }
                )
                
                if not created:
                    # Mettre à jour la séquence existante
                    sequence.prefix = prefix
                    sequence.format_pattern = format_pattern
                    sequence.auto_generation = auto_generation
                    sequence.current_year = current_year
                    sequence.save()
                
                action = "créée" if created else "mise à jour"
                messages.success(request, f"Séquence {sequence.get_sequence_type_display()} {action} avec succès")
            else:
                messages.error(request, "Aucune année scolaire active trouvée")
        else:
            messages.error(request, "Tous les champs sont obligatoires")
        
        return redirect('settings:matricule_settings')
    
    # Affichage des séquences existantes
    sequences = {}
    for seq_type, seq_name in MatriculeSequence.SEQUENCE_TYPES:
        try:
            sequence = MatriculeSequence.objects.get(sequence_type=seq_type)
            sequences[seq_type] = sequence
        except MatriculeSequence.DoesNotExist:
            sequences[seq_type] = None
    
    context = {
        'sequences': sequences,
        'sequence_types': MatriculeSequence.SEQUENCE_TYPES
    }
    
    return render(request, 'settings/matricule_settings.html', context)

@login_required
@require_http_methods(["POST"])
def update_matricule_sequence(request, sequence_id):
    """Mettre à jour une séquence de matricule"""
    try:
        sequence = get_object_or_404(MatriculeSequence, id=sequence_id)
        
        # Récupérer les données du formulaire
        prefix = request.POST.get('prefix')
        format_pattern = request.POST.get('format_pattern')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        if not prefix:
            messages.error(request, "Le préfixe est obligatoire")
            return redirect('settings:matricule_settings')
        
        if not format_pattern:
            messages.error(request, "Le format est obligatoire")
            return redirect('settings:matricule_settings')
        
        # Mettre à jour la séquence
        sequence.prefix = prefix
        sequence.format_pattern = format_pattern
        sequence.is_active = is_active
        sequence.save()
        
        messages.success(request, f"Séquence {sequence.get_sequence_type_display()} mise à jour avec succès")
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la mise à jour: {str(e)}")
    
    return redirect('settings:matricule_settings')

@login_required
@require_http_methods(["POST"])
def reset_sequence(request, sequence_id):
    """Remettre à zéro une séquence"""
    try:
        sequence = get_object_or_404(MatriculeSequence, id=sequence_id)
        sequence.last_number = 0
        sequence.save()
        
        messages.success(request, f"Séquence {sequence.get_sequence_type_display()} remise à zéro")
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la remise à zéro: {str(e)}")
    
    return redirect('settings:matricule_settings')

@login_required
def generate_test_matricule(request, sequence_id):
    """Générer un matricule de test pour une séquence"""
    try:
        sequence = get_object_or_404(MatriculeSequence, id=sequence_id)
        test_matricule = sequence.generate_matricule()
        
        return JsonResponse({
            'success': True,
            'matricule': test_matricule,
            'message': f"Matricule de test généré: {test_matricule}"
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f"Erreur lors de la génération: {str(e)}"
        })

@login_required
def get_sequence_info(request, sequence_type):
    """Récupérer les informations sur une séquence"""
    try:
        info = MatriculeService.get_sequence_info(sequence_type)
        return JsonResponse({
            'success': True,
            'info': info
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@admin_or_direction_required
def user_accounts_management(request):
    """Vue pour gérer les comptes utilisateurs des enseignants"""
    from django.db import models
    
    # Statistiques des enseignants
    teachers_total = Teacher.objects.filter(is_active=True).count()
    teachers_with_account = Teacher.objects.filter(is_active=True, user__isnull=False).count()
    teachers_without_account = Teacher.objects.filter(
        is_active=True, 
        user__isnull=True
    ).exclude(email__isnull=True).exclude(email__exact='').count()
    
    teachers_without_email = Teacher.objects.filter(
        is_active=True,
        user__isnull=True
    ).filter(models.Q(email__isnull=True) | models.Q(email__exact='')).count()
    
    # Liste des enseignants sans compte (avec email)
    teachers_list = Teacher.objects.filter(
        is_active=True, 
        user__isnull=True
    ).exclude(email__isnull=True).exclude(email__exact='').order_by('last_name', 'first_name')
    
    # Liste des enseignants avec compte pour modification de mot de passe
    teachers_with_accounts = Teacher.objects.filter(
        is_active=True, 
        user__isnull=False
    ).select_related('user').order_by('last_name', 'first_name')
    
    context = {
        'teachers_total': teachers_total,
        'teachers_with_account': teachers_with_account,
        'teachers_without_account': teachers_without_account,
        'teachers_without_email': teachers_without_email,
        'teachers_list': teachers_list,
        'teachers_with_accounts': teachers_with_accounts,
    }
    
    return render(request, 'settings/user_accounts_management.html', context)

@admin_or_direction_required
@require_http_methods(["POST"])
def create_teacher_accounts_bulk(request):
    """Créer des comptes utilisateurs en masse pour les enseignants sélectionnés"""
    
    teacher_ids = request.POST.getlist('teacher_ids')
    if not teacher_ids:
        messages.error(request, "Aucun enseignant sélectionné.")
        return redirect('settings:user_accounts_management')
    
    created_count = 0
    error_count = 0
    email_sent_count = 0
    
    base_url = getattr(settings, 'BASE_URL', request.build_absolute_uri('/'))
    login_url = f"{base_url}auth/login/"
    
    with transaction.atomic():
        for teacher_id in teacher_ids:
            try:
                teacher = Teacher.objects.get(id=teacher_id, is_active=True, user__isnull=True)
                
                if not teacher.email:
                    error_count += 1
                    continue
                
                # Générer les identifiants
                username = generate_username(teacher.first_name, teacher.last_name)
                password = generate_secure_password()
                
                # Créer l'utilisateur
                user = User.objects.create(
                    username=username,
                    first_name=teacher.first_name,
                    last_name=teacher.last_name,
                    email=teacher.email,
                    role='PROFESSEUR',
                    is_active=True
                )
                user.set_password(password)
                user.save()
                
                # Lier l'enseignant
                teacher.user = user
                teacher.save()
                
                created_count += 1
                
                # Envoyer l'email
                try:
                    send_account_creation_email(teacher, username, password, login_url)
                    email_sent_count += 1
                except Exception as e:
                    # Email failed but account created
                    pass
                    
            except Exception as e:
                error_count += 1
    
    # Messages de confirmation
    if created_count > 0:
        messages.success(
            request, 
            f"{created_count} compte(s) créé(s) avec succès. {email_sent_count} email(s) envoyé(s)."
        )
    
    if error_count > 0:
        messages.warning(request, f"{error_count} erreur(s) rencontrée(s).")
    
    return redirect('settings:user_accounts_management')

@admin_or_direction_required
@require_http_methods(["POST"])
def reset_teacher_password(request, teacher_id):
    """Réinitialiser le mot de passe d'un enseignant"""
    
    teacher = get_object_or_404(Teacher, id=teacher_id, user__isnull=False)
    
    # Générer un nouveau mot de passe
    new_password = generate_secure_password()
    
    # Mettre à jour le mot de passe
    teacher.user.set_password(new_password)
    teacher.user.save()
    
    # Envoyer l'email avec le nouveau mot de passe
    try:
        base_url = getattr(settings, 'BASE_URL', request.build_absolute_uri('/'))
        login_url = f"{base_url}auth/login/"
        send_password_reset_email(teacher, teacher.user.username, new_password, login_url)
        
        messages.success(
            request, 
            f"Mot de passe réinitialisé pour {teacher.first_name} {teacher.last_name}. "
            f"Nouvel email envoyé à {teacher.email}."
        )
    except Exception as e:
        messages.error(
            request,
            f"Mot de passe réinitialisé mais erreur lors de l'envoi de l'email : {str(e)}"
        )
    
    return redirect('settings:user_accounts_management')

# Fonctions utilitaires

def generate_username(first_name, last_name):
    """Génère un nom d'utilisateur unique"""
    base_username = f"{first_name.lower()}.{last_name.lower()}"
    base_username = ''.join(c for c in base_username if c.isalnum() or c == '.')
    
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def generate_secure_password(length=12):
    """Génère un mot de passe sécurisé"""
    characters = string.ascii_letters + string.digits + "!@#$%&*"
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password

def send_account_creation_email(teacher, username, password, login_url):
    """Envoie l'email de création de compte"""
    subject = f"🎓 EduManager - Votre compte enseignant"
    
    message = f"""
Bonjour {teacher.first_name} {teacher.last_name},

Un compte utilisateur a été créé pour vous sur EduManager.

Vos identifiants de connexion :
• Nom d'utilisateur : {username}
• Mot de passe : {password}
• URL de connexion : {login_url}

IMPORTANT : Changez votre mot de passe lors de votre première connexion.

Avec votre compte, vous pouvez :
• Consulter vos classes et matières assignées
• Saisir et modifier les notes de vos élèves
• Consulter les emplois du temps
• Accéder aux informations des élèves de vos classes

Cordialement,
L'équipe EduManager
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[teacher.email],
        fail_silently=False,
    )

def send_password_reset_email(teacher, username, new_password, login_url):
    """Envoie l'email de réinitialisation de mot de passe"""
    subject = f"🔐 EduManager - Mot de passe réinitialisé"
    
    message = f"""
Bonjour {teacher.first_name} {teacher.last_name},

Votre mot de passe EduManager a été réinitialisé par un administrateur.

Vos nouveaux identifiants :
• Nom d'utilisateur : {username}
• Nouveau mot de passe : {new_password}
• URL de connexion : {login_url}

IMPORTANT : Changez ce mot de passe temporaire lors de votre prochaine connexion.

Si vous n'avez pas demandé cette réinitialisation, contactez immédiatement l'administration.

Cordialement,
L'équipe EduManager
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[teacher.email],
        fail_silently=False,
    )
