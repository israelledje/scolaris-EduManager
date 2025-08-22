# 🚀 Guide de Migration - Génération des Comptes Parents

## 📋 **Vue d'ensemble**

Ce guide explique comment générer automatiquement les comptes parents pour tous les guardians existants dans votre système Scolaris.

## 🔧 **Prérequis**

### **1. Configuration de l'Application**
Assurez-vous que l'application `parents_portal` est ajoutée à vos `INSTALLED_APPS` :

```python
# settings.py
INSTALLED_APPS = [
    # ... autres applications
    'parents_portal',
]
```

### **2. Configuration Email**
Configurez l'envoi d'emails dans vos paramètres :

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # ou votre serveur SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre.email@gmail.com'
EMAIL_HOST_PASSWORD = 'votre_mot_de_passe_app'
DEFAULT_FROM_EMAIL = 'SCOLARIS <noreply@scolaris.com>'
```

### **3. Exécution des Migrations**
Créez et appliquez les migrations de la base de données :

```bash
python manage.py makemigrations parents_portal
python manage.py migrate
```

## 🎯 **Génération des Comptes Parents**

### **Option 1 : Génération en Masse (Recommandée)**

Génère les comptes pour tous les guardians existants :

```bash
python manage.py generate_parent_accounts
```

**Options disponibles :**
- `--dry-run` : Simule la création sans créer réellement les comptes
- `--force` : Force la création même si des comptes existent déjà
- `--email-only` : Génère seulement les comptes pour les guardians avec email

**Exemples d'utilisation :**

```bash
# Simulation (recommandé pour tester)
python manage.py generate_parent_accounts --dry-run

# Génération pour guardians avec email uniquement
python manage.py generate_parent_accounts --email-only

# Génération forcée (remplace les comptes existants)
python manage.py generate_parent_accounts --force

# Génération complète
python manage.py generate_parent_accounts
```

### **Option 2 : Génération pour un Guardian Spécifique**

Génère le compte pour un guardian particulier :

```bash
python manage.py generate_parent_accounts --guardian-id 123
```

### **Option 3 : Renvoi des Identifiants**

Renvoie les identifiants aux parents existants :

```bash
python manage.py generate_parent_accounts --resend-credentials
```

## 📊 **Vérification de l'État des Comptes**

### **Vérification Générale**

```bash
python manage.py check_parent_accounts
```

**Options disponibles :**
- `--detailed` : Affiche des détails sur chaque compte
- `--orphaned` : Affiche seulement les comptes orphelins (sans étudiants)
- `--inactive` : Affiche seulement les comptes inactifs

**Exemples d'utilisation :**

```bash
# Vérification générale
python manage.py check_parent_accounts

# Vérification détaillée
python manage.py check_parent_accounts --detailed

# Vérification des comptes orphelins
python manage.py check_parent_accounts --orphaned

# Vérification des comptes inactifs
python manage.py check_parent_accounts --inactive
```

## 🛠️ **Utilisation des Utilitaires Python**

### **Génération en Masse via Code**

```python
from parents_portal.utils import ParentAccountManager

# Générer tous les comptes
manager = ParentAccountManager()
stats = manager.bulk_create_parent_accounts()

print(f"Comptes créés: {stats['created']}")
print(f"Échecs: {stats['failed']}")
```

### **Renvoi des Identifiants**

```python
# Renvoyer les identifiants à tous les parents
stats = manager.resend_credentials_to_parents(force_new_password=True)

print(f"Emails envoyés: {stats['emails_sent']}")
```

### **Nettoyage des Comptes Orphelins**

```python
# Nettoyer les comptes sans étudiants
cleanup_stats = manager.cleanup_orphaned_accounts()

print(f"Comptes désactivés: {cleanup_stats['deactivated']}")
```

### **Validation des Comptes**

```python
# Valider l'intégrité des comptes
validation_results = manager.validate_parent_accounts()

print(f"Comptes valides: {validation_results['valid']}")
print(f"Comptes invalides: {validation_results['invalid']}")
```

### **Statistiques Détaillées**

```python
# Obtenir des statistiques complètes
stats = manager.get_parent_statistics()

print(f"Couverture: {stats['coverage_percentage']:.1f}%")
print(f"Comptes actifs: {stats['active_percentage']:.1f}%")
```

## 📧 **Gestion des Emails**

### **Envoi de Notifications**

```python
from parents_portal.utils import send_parent_notification_email

# Envoyer une notification à un parent
success = send_parent_notification_email(
    parent=parent_user,
    subject="Nouvelle notification",
    message="Votre enfant a reçu une nouvelle note."
)
```

### **Export des Données**

```python
from parents_portal.utils import export_parent_accounts_to_csv

# Exporter tous les comptes vers un fichier CSV
success = export_parent_accounts_to_csv('comptes_parents.csv')
```

## 🔍 **Surveillance et Maintenance**

### **Tâches Cron Recommandées**

Ajoutez ces tâches à votre crontab pour la maintenance automatique :

```bash
# Vérification quotidienne de l'état des comptes
0 8 * * * cd /path/to/scolaris && python manage.py check_parent_accounts

# Nettoyage hebdomadaire des comptes orphelins
0 9 * * 0 cd /path/to/scolaris && python manage.py cleanup_orphaned_accounts

# Rappels de paiement automatiques (si implémenté)
0 10 * * * cd /path/to/scolaris && python manage.py send_payment_reminders
```

### **Logs et Monitoring**

Surveillez les logs Django pour détecter les problèmes :

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/parents_portal.log',
        },
    },
    'loggers': {
        'parents_portal': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🚨 **Dépannage**

### **Problèmes Courants**

1. **Erreur de migration**
   ```bash
   python manage.py makemigrations --empty parents_portal
   python manage.py migrate
   ```

2. **Problème d'email**
   ```bash
   # Tester la configuration email
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Message test', 'from@test.com', ['to@test.com'])
   ```

3. **Comptes non créés**
   ```bash
   # Vérifier les guardians sans email
   python manage.py check_parent_accounts --detailed
   ```

### **Vérification de l'Installation**

```bash
# Vérifier que l'application est installée
python manage.py check --deploy

# Lister les commandes disponibles
python manage.py help | grep parent
```

## 📈 **Processus de Migration Recommandé**

### **Phase 1 : Préparation**
1. Sauvegardez votre base de données
2. Testez la configuration email
3. Exécutez en mode simulation

### **Phase 2 : Migration**
1. Générez les comptes en masse
2. Vérifiez l'état des comptes
3. Testez la connexion de quelques parents

### **Phase 3 : Validation**
1. Vérifiez l'intégrité des données
2. Testez les fonctionnalités du portail
3. Surveillez les logs et erreurs

### **Phase 4 : Production**
1. Activez les notifications automatiques
2. Configurez la maintenance automatique
3. Formez les utilisateurs

## 🎉 **Succès de la Migration**

Une fois la migration terminée, vous devriez voir :

- ✅ Tous les guardians avec email ont un compte parent
- ✅ Les identifiants ont été envoyés par email
- ✅ Les relations parent-étudiant sont créées
- ✅ Le portail parents est accessible
- ✅ Les notifications automatiques fonctionnent

## 📞 **Support**

En cas de problème :

1. Consultez les logs Django
2. Vérifiez la configuration email
3. Utilisez les commandes de vérification
4. Consultez la documentation complète

---

**Version** : 1.0.0  
**Dernière mise à jour** : 2025-01-21  
**Statut** : Production Ready ✅
