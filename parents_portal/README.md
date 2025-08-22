# Portail Parents - Scolaris

## 🎯 **Vue d'ensemble**

Le portail parents est une application dédiée permettant aux parents et tuteurs d'élèves d'accéder aux informations scolaires de leurs enfants via une interface web sécurisée.

## ✨ **Fonctionnalités Principales**

### 🔐 **Authentification Automatique**
- **Génération automatique** des comptes parents à partir des guardians existants
- **Envoi automatique** des identifiants par email
- **Système de sécurité** avec tokens de vérification
- **Gestion des sessions** avec traçabilité des connexions

### 👨‍👩‍👧‍👦 **Gestion des Relations**
- **Relations parent-étudiant** avec permissions granulaires
- **Support multi-étudiants** par parent
- **Gestion des rôles** (Père, Mère, Tuteur, Responsable légal)
- **Permissions personnalisables** par relation

### 📊 **Suivi Académique**
- **Consultation des notes** en temps réel
- **Accès aux bulletins** avec historique complet
- **Statistiques de performance** par matière et séquence
- **Suivi de la présence** avec taux d'assiduité

### 💰 **Gestion Financière**
- **Vue d'ensemble** de la situation financière
- **Détail des tranches** avec statuts (payé, partiel, en retard)
- **Paiements en ligne** via Orange Money et MTN Mobile Money
- **Historique des transactions** avec reçus
- **Calcul automatique** des frais selon la méthode de paiement

### 🔔 **Système de Notifications**
- **Notifications automatiques** pour les nouveaux bulletins
- **Alertes de paiement** et rappels d'échéances
- **Notifications push** et emails
- **Centre de notifications** centralisé

## 🏗️ **Architecture Technique**

### **Modèles de Données**
- `ParentUser` : Utilisateur parent avec authentification
- `ParentStudentRelation` : Relation parent-étudiant avec permissions
- `ParentPaymentMethod` : Méthodes de paiement enregistrées
- `ParentPayment` : Historique des paiements effectués
- `ParentNotification` : Système de notifications
- `ParentLoginSession` : Traçabilité des connexions

### **Services**
- `ParentPortalService` : Logique métier principale
- `PaymentService` : Gestion des paiements et intégrations

### **Signaux Automatiques**
- Création automatique des comptes parents
- Notifications automatiques pour les bulletins
- Gestion des changements de statut des paiements
- Rappels automatiques d'échéances

## 🚀 **Installation et Configuration**

### **1. Ajouter l'application aux INSTALLED_APPS**
```python
INSTALLED_APPS = [
    # ... autres applications
    'parents_portal',
]
```

### **2. Inclure les URLs dans le projet principal**
```python
# urls.py principal
urlpatterns = [
    # ... autres URLs
    path('parents/', include('parents_portal.urls')),
]
```

### **3. Configurer l'authentification personnalisée**
```python
# settings.py
AUTH_USER_MODEL = 'parents_portal.ParentUser'
```

### **4. Exécuter les migrations**
```bash
python manage.py makemigrations parents_portal
python manage.py migrate
```

## 📧 **Configuration Email**

### **Variables d'environnement requises**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=votre.email@gmail.com
EMAIL_PASSWORD=votre_mot_de_passe_app
DEFAULT_FROM_EMAIL=SCOLARIS <noreply@scolaris.com>
```

### **Test de la configuration**
```python
from django.core.mail import send_mail
send_mail('Test', 'Message de test', 'from@example.com', ['to@example.com'])
```

## 🔌 **Intégrations de Paiement**

### **Orange Money (OM)**
- API REST pour l'initiation des paiements
- Webhooks pour les notifications de statut
- Gestion des frais selon les montants

### **MTN Mobile Money (MOMO)**
- Intégration similaire à Orange Money
- Support des différents types de comptes
- Gestion des erreurs et retry automatique

### **Simulation en Développement**
- Mode simulation pour les tests
- Création automatique des transactions
- Validation des processus de paiement

## 🛡️ **Sécurité et Permissions**

### **Authentification**
- Mots de passe temporaires générés automatiquement
- Changement obligatoire au premier login
- Sessions sécurisées avec traçabilité IP

### **Autorisations**
- Accès limité aux étudiants associés
- Permissions granulaires par fonctionnalité
- Audit trail des actions effectuées

### **Protection des Données**
- Chiffrement des informations sensibles
- Logs de sécurité complets
- Conformité RGPD intégrée

## 📱 **Interface Utilisateur**

### **Design Responsive**
- Interface adaptée mobile et desktop
- Navigation intuitive et accessible
- Thème cohérent avec l'application principale

### **Fonctionnalités UX**
- Tableau de bord personnalisé
- Filtres et recherche avancés
- Notifications en temps réel
- Export des données (PDF, Excel)

## 🔧 **Maintenance et Monitoring**

### **Logs et Surveillance**
- Logs détaillés des actions utilisateurs
- Monitoring des performances
- Alertes automatiques en cas d'erreur

### **Sauvegarde et Récupération**
- Sauvegarde automatique des données
- Procédures de récupération documentées
- Tests de restauration réguliers

### **Mises à Jour**
- Gestion des versions de l'application
- Procédures de déploiement sécurisées
- Rollback automatique en cas de problème

## 📚 **Documentation API**

### **Endpoints Principaux**
- `POST /parents/login/` : Connexion parent
- `GET /parents/dashboard/` : Tableau de bord
- `GET /parents/students/` : Liste des étudiants
- `POST /parents/finances/payment/` : Effectuer un paiement
- `GET /parents/notifications/` : Notifications

### **Webhooks**
- `POST /parents/api/payment-webhook/` : Notifications de paiement
- Support des signatures de sécurité
- Validation automatique des données

## 🚨 **Dépannage**

### **Problèmes Courants**
1. **Email non envoyé** : Vérifier la configuration SMTP
2. **Paiement échoué** : Contrôler les logs de l'API de paiement
3. **Permissions manquantes** : Vérifier les relations parent-étudiant

### **Logs de Diagnostic**
```python
import logging
logger = logging.getLogger('parents_portal')
logger.setLevel(logging.DEBUG)
```

## 🤝 **Support et Contribution**

### **Contact**
- **Développeur** : Équipe Scolaris
- **Email** : support@scolaris.com
- **Documentation** : [Wiki interne]

### **Contribution**
- Code review obligatoire
- Tests unitaires requis
- Documentation des nouvelles fonctionnalités

---

**Version** : 1.0.0  
**Dernière mise à jour** : 2025-01-21  
**Statut** : Production Ready ✅
