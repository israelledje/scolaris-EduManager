# Système de Notification SCOLARIS

Ce module gère l'envoi automatique de notifications par email et SMS aux parents/tuteurs après validation des paiements.

## 🚀 Fonctionnalités

- **Notifications de paiement** : Envoi automatique après validation d'un paiement de tranche
- **Notifications d'inscription** : Envoi automatique après validation des frais d'inscription
- **Support multi-canal** : Email et SMS simultanés
- **Templates personnalisés** : Emails HTML et texte avec design professionnel
- **Gestion d'erreurs** : Logging détaillé et fallback gracieux

## 📧 Configuration Email

### 1. Configuration SMTP dans `settings.py`

```python
# Configuration Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Ou votre serveur SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@gmail.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe-app'
DEFAULT_FROM_EMAIL = 'SCOLARIS <noreply@scolaris.com>'
```

### 2. Configuration Gmail (recommandé pour les tests)

1. Activez l'authentification à 2 facteurs sur votre compte Gmail
2. Générez un mot de passe d'application
3. Utilisez ce mot de passe dans `EMAIL_HOST_PASSWORD`

### 3. Configuration serveur SMTP personnalisé

```python
EMAIL_HOST = 'votre-serveur-smtp.com'
EMAIL_PORT = 587  # ou 465 pour SSL
EMAIL_USE_TLS = True  # ou False pour SSL
EMAIL_HOST_USER = 'votre-utilisateur'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe'
```

## 📱 Configuration SMS (API SMSVAS)

### 1. Configuration dans `settings.py`

```python
# Configuration SMS (API SMSVAS)
SMS_USER = 'votre-username-sms'
SMS_PASSWORD = 'votre-password-sms'
SMS_SENDER_ID = 'SCOLARIS'
```

### 2. Obtention des identifiants SMSVAS

1. Créez un compte sur [SMSVAS](https://smsvas.com)
2. Récupérez votre username et password
3. Configurez votre sender ID (doit être approuvé)

### 3. Test de l'API SMS

```bash
python test_notifications.py
```

## 🔧 Utilisation

### 1. Notifications automatiques

Les notifications sont envoyées automatiquement après :
- Création d'un paiement de tranche (`/finances/payments/create/`)
- Création d'un paiement d'inscription (`/finances/payments/inscription/create/`)

### 2. Utilisation manuelle

```python
from notifications.services import notification_service

# Notification de paiement
payment_data = {
    'student_name': 'Nom Prénom',
    'tranche_number': 1,
    'class_name': '6ème A',
    'school_year': '2024-2025',
    'amount': 50000,
    'payment_mode': 'Espèces',
    'receipt_number': 'REC-001',
    'payment_date': '01/12/2024',
    'guardian_email': 'parent@example.com',
    'guardian_phone': '237612345678',
    'school_phone': '237612345679',
    'school_email': 'contact@scolaris.com',
}

results = notification_service.send_payment_notification(payment_data)
```

### 3. Vérification des résultats

```python
if results['email_sent']:
    print("✅ Email envoyé avec succès")
if results['sms_sent']:
    print("✅ SMS envoyé avec succès")
if results['errors']:
    print(f"⚠️ Erreurs: {results['errors']}")
```

## 📋 Prérequis

### 1. Modèles requis

- `Student` avec relation `guardians`
- `Guardian` avec champs `email` et `phone`
- `School` avec champs `phone` et `email` (optionnels)

### 2. Dépendances

```bash
pip install requests  # Pour l'API SMS
```

## 🧪 Tests

### 1. Test complet

```bash
python test_notifications.py
```

### 2. Test individuel

```python
# Test email uniquement
python manage.py shell
from notifications.services import notification_service
# ... test code
```

## 📝 Logs

Le système de notification génère des logs détaillés :

- **Succès** : Confirmation d'envoi des notifications
- **Avertissements** : Échecs partiels (email ou SMS uniquement)
- **Erreurs** : Échecs complets avec détails

### Niveaux de log

- `INFO` : Notifications envoyées avec succès
- `WARNING` : Échecs partiels
- `ERROR` : Erreurs générales

## 🚨 Dépannage

### 1. Emails non envoyés

- Vérifiez la configuration SMTP
- Testez avec `python test_notifications.py`
- Vérifiez les logs Django

### 2. SMS non envoyés

- Vérifiez les identifiants SMSVAS
- Testez l'API directement
- Vérifiez le solde du compte SMS

### 3. Erreurs de template

- Vérifiez que les templates existent
- Vérifiez la syntaxe Django
- Testez le rendu manuellement

## 🔒 Sécurité

- Les mots de passe sont stockés dans `settings.py`
- Utilisez des variables d'environnement en production
- Limitez l'accès aux comptes SMS et email

## 📚 Ressources

- [Documentation Django Email](https://docs.djangoproject.com/en/stable/topics/email/)
- [API SMSVAS](https://smsvas.com/bulk/public/index.php/api/v1/sendsms)
- [Gestion des erreurs Django](https://docs.djangoproject.com/en/stable/howto/error-reporting/)

## 🤝 Support

Pour toute question ou problème :
1. Vérifiez les logs Django
2. Testez avec le script de test
3. Consultez la documentation
4. Contactez l'équipe de développement
