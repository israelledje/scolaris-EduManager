#!/usr/bin/env python
"""
Script de test pour vérifier la configuration email
"""

import os
import sys
import django

# Ajouter le chemin vers le projet Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_configuration():
    """Teste l'envoi d'un email simple"""
    
    print("🧪 Test de la configuration email...")
    print("=" * 50)
    
    # Vérifier la configuration
    print(f"📧 Backend Email : {settings.EMAIL_BACKEND}")
    print(f"🏠 Serveur SMTP : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"👤 Utilisateur : {settings.EMAIL_HOST_USER}")
    print(f"🔒 SSL activé : {settings.EMAIL_USE_SSL}")
    print(f"📤 Email expéditeur : {settings.DEFAULT_FROM_EMAIL}")
    
    # Demander l'email de test
    test_email = input(f"\n✉️  Entrez votre email pour recevoir un test : ").strip()
    
    if not test_email:
        print("❌ Email requis pour le test.")
        return
    
    try:
        # Envoyer l'email de test
        print(f"\n📤 Envoi de l'email de test à {test_email}...")
        
        subject = "🧪 Test EduManager - Configuration Email"
        message = """
Bonjour,

Ceci est un email de test pour vérifier la configuration d'EduManager.

Si vous recevez cet email, la configuration fonctionne correctement ! ✅

Informations techniques :
- Date/Heure : """ + str(django.utils.timezone.now()) + """
- Serveur : """ + settings.EMAIL_HOST + """
- Backend : """ + settings.EMAIL_BACKEND + """

Cordialement,
L'équipe EduManager
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
        )
        
        print("✅ Email de test envoyé avec succès !")
        print("📬 Vérifiez votre boîte de réception (et les spams).")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {str(e)}")
        print("\n💡 Vérifications à faire :")
        print("   1. Variables d'environnement EMAIL_USER et EMAIL_PASSWORD")
        print("   2. Configuration du serveur SMTP")
        print("   3. Autorisations dans votre compte email")
        print("   4. Connexion internet")

if __name__ == "__main__":
    from django.utils import timezone
    test_email_configuration()
