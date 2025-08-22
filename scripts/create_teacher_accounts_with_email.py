#!/usr/bin/env python
"""
Script pour créer automatiquement des comptes utilisateurs pour les enseignants
et envoyer les identifiants par email.

Ce script :
1. Parcourt tous les enseignants actifs sans compte utilisateur
2. Crée un compte utilisateur avec login/password
3. Envoie automatiquement les identifiants par email
4. Génère un rapport détaillé
"""

import os
import sys
import django
import string
import secrets
from datetime import datetime

# Ajouter le chemin vers le projet Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from authentication.models import User
from teachers.models import Teacher

def generate_secure_password(length=12):
    """Génère un mot de passe sécurisé"""
    # Caractères autorisés : lettres, chiffres, quelques symboles
    characters = string.ascii_letters + string.digits + "!@#$%&*"
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password

def generate_username(first_name, last_name):
    """Génère un nom d'utilisateur unique"""
    # Base : prénom.nom en minuscules
    base_username = f"{first_name.lower()}.{last_name.lower()}"
    
    # Nettoyer les caractères spéciaux
    base_username = ''.join(c for c in base_username if c.isalnum() or c == '.')
    
    # Vérifier l'unicité
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def create_email_template():
    """Crée un template d'email pour les nouveaux comptes"""
    template_content = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1e40af, #3730a3); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }
        .credentials { background: white; border: 2px solid #e9ecef; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .credential-item { margin: 10px 0; padding: 8px; background: #f1f3f4; border-left: 4px solid #1e40af; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; font-size: 12px; color: #666; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 EduManager - Accès au Système</h1>
            <p>Bienvenue dans votre espace enseignant</p>
        </div>
        
        <div class="content">
            <h2>Bonjour {{ teacher_name }},</h2>
            
            <p>Un compte utilisateur a été créé pour vous permettre d'accéder au système de gestion scolaire <strong>EduManager</strong>.</p>
            
            <div class="credentials">
                <h3>🔑 Vos identifiants de connexion :</h3>
                <div class="credential-item">
                    <strong>Nom d'utilisateur :</strong> {{ username }}
                </div>
                <div class="credential-item">
                    <strong>Mot de passe :</strong> {{ password }}
                </div>
                <div class="credential-item">
                    <strong>URL de connexion :</strong> <a href="{{ login_url }}">{{ login_url }}</a>
                </div>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important :</strong><br>
                • Changez votre mot de passe lors de votre première connexion<br>
                • Gardez vos identifiants confidentiels<br>
                • Contactez l'administration en cas de problème
            </div>
            
            <h3>🎯 Avec votre compte, vous pouvez :</h3>
            <ul>
                <li>Consulter vos classes et matières assignées</li>
                <li>Saisir et modifier les notes de vos élèves</li>
                <li>Consulter les emplois du temps</li>
                <li>Accéder aux informations des élèves de vos classes</li>
            </ul>
            
            <p>Si vous avez des questions ou rencontrez des difficultés, n'hésitez pas à contacter l'équipe administrative.</p>
            
            <p>Cordialement,<br>
            <strong>L'équipe EduManager</strong></p>
        </div>
        
        <div class="footer">
            <p>Cet email a été généré automatiquement le {{ date_created }}.</p>
            <p>© {{ year }} EduManager - Système de Gestion Scolaire</p>
        </div>
    </div>
</body>
</html>
    '''
    
    # Créer le répertoire templates s'il n'existe pas
    template_dir = os.path.join(os.path.dirname(__file__), 'email_templates')
    os.makedirs(template_dir, exist_ok=True)
    
    # Sauvegarder le template
    template_path = os.path.join(template_dir, 'teacher_account_created.html')
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    return template_path

def send_account_email(teacher, username, password, login_url):
    """Envoie l'email avec les identifiants au nouvel enseignant"""
    try:
        # Préparer le contexte pour le template
        context = {
            'teacher_name': f"{teacher.first_name} {teacher.last_name}",
            'username': username,
            'password': password,
            'login_url': login_url,
            'date_created': datetime.now().strftime('%d/%m/%Y à %H:%M'),
            'year': datetime.now().year
        }
        
        # Créer le contenu HTML
        template_path = create_email_template()
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Remplacer les variables dans le template
        for key, value in context.items():
            html_content = html_content.replace('{{ ' + key + ' }}', str(value))
        
        # Contenu text simple (fallback)
        text_content = f"""
Bonjour {context['teacher_name']},

Un compte utilisateur a été créé pour vous sur EduManager.

Vos identifiants de connexion :
- Nom d'utilisateur : {username}
- Mot de passe : {password}
- URL de connexion : {login_url}

IMPORTANT : Changez votre mot de passe lors de votre première connexion.

Cordialement,
L'équipe EduManager
        """
        
        # Envoyer l'email
        from django.core.mail import EmailMultiAlternatives
        
        subject = f"🎓 EduManager - Votre compte enseignant créé"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@edumanager.com')
        to_email = [teacher.email]
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        return True, "Email envoyé avec succès"
        
    except Exception as e:
        return False, f"Erreur lors de l'envoi de l'email : {str(e)}"

def create_teacher_accounts_with_email():
    """
    Fonction principale pour créer les comptes enseignants et envoyer les emails
    """
    print("🚀 Démarrage du processus de création de comptes enseignants...")
    print("=" * 70)
    
    # Vérifier la configuration email
    if not hasattr(settings, 'EMAIL_BACKEND'):
        print("⚠️  ATTENTION : Configuration email non trouvée dans settings.py")
        print("   Les emails ne pourront pas être envoyés.")
        continue_anyway = input("   Continuer quand même ? (o/N) : ").lower().strip()
        if continue_anyway != 'o':
            print("❌ Processus annulé.")
            return
    
    # Récupérer les enseignants actifs sans compte utilisateur
    teachers_without_account = Teacher.objects.filter(
        is_active=True,
        user__isnull=True
    ).exclude(email__isnull=True).exclude(email__exact='')
    
    teachers_without_email = Teacher.objects.filter(
        is_active=True,
        user__isnull=True
    ).filter(models.Q(email__isnull=True) | models.Q(email__exact=''))
    
    print(f"📊 ÉTAT ACTUEL DE LA BASE DE DONNÉES")
    print(f"   • Enseignants actifs sans compte et avec email : {teachers_without_account.count()}")
    print(f"   • Enseignants actifs sans compte et sans email : {teachers_without_email.count()}")
    print(f"   • Total à traiter : {teachers_without_account.count()}")
    
    if teachers_without_email.exists():
        print(f"\n⚠️  ENSEIGNANTS SANS EMAIL (ignorés) :")
        for teacher in teachers_without_email[:5]:
            print(f"   - {teacher.first_name} {teacher.last_name} ({teacher.matricule})")
        if teachers_without_email.count() > 5:
            print(f"   ... et {teachers_without_email.count() - 5} autres")
    
    if teachers_without_account.count() == 0:
        print("\n✅ Tous les enseignants actifs avec email ont déjà un compte utilisateur.")
        return
    
    # Demander confirmation
    print(f"\n🔔 CONFIRMATION")
    print(f"   Créer {teachers_without_account.count()} comptes utilisateurs et envoyer les emails ?")
    confirmation = input("   Tapez 'CONFIRMER' pour continuer : ").strip()
    
    if confirmation != 'CONFIRMER':
        print("❌ Processus annulé.")
        return
    
    # URL de base pour la connexion
    base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
    login_url = f"{base_url}/auth/login/"
    
    # Statistiques
    created_count = 0
    email_sent_count = 0
    errors = []
    
    print(f"\n🔧 CRÉATION DES COMPTES EN COURS...")
    print("-" * 70)
    
    with transaction.atomic():
        for teacher in teachers_without_account:
            try:
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
                
                # Lier l'enseignant à l'utilisateur
                teacher.user = user
                teacher.save()
                
                created_count += 1
                print(f"✅ Compte créé : {teacher.first_name} {teacher.last_name} → {username}")
                
                # Envoyer l'email
                email_success, email_message = send_account_email(
                    teacher, username, password, login_url
                )
                
                if email_success:
                    email_sent_count += 1
                    print(f"   📧 Email envoyé à {teacher.email}")
                else:
                    print(f"   ❌ Échec email : {email_message}")
                    errors.append(f"{teacher.first_name} {teacher.last_name}: {email_message}")
                
            except Exception as e:
                error_msg = f"Erreur pour {teacher.first_name} {teacher.last_name} : {str(e)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
    
    # Rapport final
    print("\n" + "=" * 70)
    print("📈 RAPPORT FINAL")
    print("=" * 70)
    print(f"✅ Comptes créés avec succès : {created_count}")
    print(f"📧 Emails envoyés avec succès : {email_sent_count}")
    print(f"❌ Erreurs rencontrées : {len(errors)}")
    
    if errors:
        print(f"\n🔍 DÉTAIL DES ERREURS :")
        for error in errors:
            print(f"   • {error}")
    
    if created_count > 0:
        print(f"\n💡 INFORMATIONS IMPORTANTES :")
        print(f"   • Tous les mots de passe sont générés automatiquement (12 caractères)")
        print(f"   • Les enseignants recevront leurs identifiants par email")
        print(f"   • Ils devront changer leur mot de passe à la première connexion")
        print(f"   • URL de connexion : {login_url}")
    
    print(f"\n🎉 Processus terminé avec succès !")

if __name__ == "__main__":
    # Import nécessaire pour les requêtes complexes
    from django.db import models
    
    try:
        create_teacher_accounts_with_email()
    except KeyboardInterrupt:
        print("\n\n❌ Processus interrompu par l'utilisateur.")
    except Exception as e:
        print(f"\n\n💥 ERREUR CRITIQUE : {str(e)}")
        print("Vérifiez la configuration de la base de données et des emails.")
