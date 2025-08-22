# 🎓 Guide : Création automatique de comptes enseignants

## 📋 Description

Ce script automatise la création de comptes utilisateurs pour les enseignants et l'envoi des identifiants par email.

## 🚀 Fonctionnalités

- ✅ Parcourt tous les enseignants actifs sans compte utilisateur
- ✅ Génère des identifiants sécurisés (login + mot de passe)
- ✅ Crée les comptes dans la base de données
- ✅ Envoie automatiquement les identifiants par email
- ✅ Génère un rapport détaillé
- ✅ Template d'email professionnel (HTML + texte)

## 🔧 Prérequis

### 1. Configuration Email

Dans votre fichier `.env` ou variables d'environnement :

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USER=votre-email@gmail.com
EMAIL_PASSWORD=votre-mot-de-passe-app
```

### 2. Pour Gmail (recommandé)

1. Activez la **validation en 2 étapes**
2. Créez un **mot de passe d'application** :
   - Compte Google → Sécurité → Validation en 2 étapes
   - Mots de passe des applications → Générer
3. Utilisez ce mot de passe dans `EMAIL_PASSWORD`

### 3. Autres fournisseurs

- **Outlook** : `smtp-mail.outlook.com:587` (TLS)
- **Yahoo** : `smtp.mail.yahoo.com:465` (SSL)
- **Serveur local** : Configurez selon vos paramètres

## 📖 Utilisation

### 1. Test de la configuration email

```bash
# Tester la configuration
python scripts/test_email_config.py
```

### 2. Création des comptes enseignants

```bash
# Exécuter le script principal
python scripts/create_teacher_accounts_with_email.py
```

### 3. Étapes du processus

1. **Analyse** : Le script affiche les enseignants concernés
2. **Confirmation** : Tapez `CONFIRMER` pour continuer
3. **Création** : Génération des comptes et envoi des emails
4. **Rapport** : Résumé détaillé des opérations

## 📊 Exemple de sortie

```
🚀 Démarrage du processus de création de comptes enseignants...
======================================================================

📊 ÉTAT ACTUEL DE LA BASE DE DONNÉES
   • Enseignants actifs sans compte et avec email : 5
   • Enseignants actifs sans compte et sans email : 2
   • Total à traiter : 5

🔔 CONFIRMATION
   Créer 5 comptes utilisateurs et envoyer les emails ?
   Tapez 'CONFIRMER' pour continuer : CONFIRMER

🔧 CRÉATION DES COMPTES EN COURS...
----------------------------------------------------------------------
✅ Compte créé : Marie Martin → marie.martin
   📧 Email envoyé à marie.martin@school.edu
✅ Compte créé : Jean Dupont → jean.dupont
   📧 Email envoyé à jean.dupont@school.edu
...

======================================================================
📈 RAPPORT FINAL
======================================================================
✅ Comptes créés avec succès : 5
📧 Emails envoyés avec succès : 5
❌ Erreurs rencontrées : 0

🎉 Processus terminé avec succès !
```

## 📧 Template d'email

Les enseignants reçoivent un email professionnel contenant :

- 🎯 **Identifiants de connexion** (login/password)
- 🔗 **URL de connexion directe**
- ⚠️ **Instructions de sécurité**
- 📋 **Liste des fonctionnalités accessibles**

## 🔐 Sécurité

### Mots de passe générés

- **Longueur** : 12 caractères
- **Composition** : Lettres, chiffres, symboles
- **Unicité** : Chaque mot de passe est unique
- **Cryptage** : Hashé dans la base de données

### Recommandations

- Les enseignants doivent changer leur mot de passe à la première connexion
- Gardez les emails confidentiels
- Surveillez les bounces et erreurs d'envoi

## 🛠️ Dépannage

### Erreur d'envoi d'email

```bash
❌ Erreur lors de l'envoi : SMTPAuthenticationError
```

**Solutions** :
1. Vérifiez `EMAIL_USER` et `EMAIL_PASSWORD`
2. Activez l'authentification 2FA + mot de passe d'app
3. Vérifiez la configuration SMTP

### Pas d'enseignants trouvés

```bash
✅ Tous les enseignants actifs avec email ont déjà un compte utilisateur.
```

**Normal** : Tous les comptes sont déjà créés

### Enseignants sans email

Les enseignants sans adresse email sont ignorés. Ajoutez leurs emails dans l'interface d'administration avant de relancer le script.

## 📝 Logs et suivi

- Tous les comptes créés sont tracés
- Les erreurs sont détaillées dans le rapport
- Utilisez l'admin Django pour voir les liaisons User-Teacher

## 🔄 Relancer le script

Le script est **idempotent** : 
- Il ignore les enseignants ayant déjà un compte
- Vous pouvez le relancer sans risque
- Seuls les nouveaux enseignants seront traités

## 💡 Conseils

1. **Testez d'abord** avec `test_email_config.py`
2. **Sauvegardez** la base avant les opérations massives
3. **Informez** les enseignants qu'ils vont recevoir leurs identifiants
4. **Configurez** un email de support pour les questions
