# Configuration du Système de Notifications SCOLARIS

## 🎯 Configuration Actuelle

### 📧 Email - Mode TEST (Console)
- **Backend** : `django.core.mail.backends.console.EmailBackend`
- **Fonctionnement** : Les emails sont affichés dans la console du serveur Django
- **Avantage** : Pas de configuration SMTP nécessaire pour les tests

### 📱 SMS - Variables d'Environnement
- **API** : SMSVAS
- **Configuration** : Via fichier `.env`
- **Variables** : `SMS_USER`, `SMS_PASSWORD`, `SMS_SENDER_ID`

## 🔧 Configuration Requise

### 1. Fichier .env
Créer un fichier `.env` à la racine du projet avec :

```bash
# Configuration SMS - API SMSVAS
SMS_USER=votre_username_sms
SMS_PASSWORD=votre_password_sms
SMS_SENDER_ID=SCOLARIS

# Configuration Email (optionnel pour la production)
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=votre_email@gmail.com
# EMAIL_HOST_PASSWORD=votre_app_password
```

### 2. Installation des Dépendances
```bash
pip install python-dotenv requests
```

## 🧪 Test du Système

### Test Automatique
```bash
python test_notifications_env.py
```

### Test Manuel
1. Démarrer le serveur Django
2. Créer un paiement
3. Vérifier la console pour les emails
4. Vérifier les logs pour les SMS

## 📊 Fonctionnement

### Notifications Automatiques
- **Paiements de tranches** : Email + SMS automatiques
- **Paiements d'inscription** : Email + SMS automatiques
- **Destinataires** : Parents/tuteurs via le modèle Guardian

### Flux de Notification
1. **Paiement créé** → Vue Django
2. **Service de notification** appelé automatiquement
3. **Email** → Affiché dans la console (mode test)
4. **SMS** → Envoyé via API SMSVAS
5. **Résultats** → Loggés et affichés à l'utilisateur

## 🔍 Logs et Monitoring

### Emplacement des Logs
- **Console** : Affichage en temps réel
- **Fichier principal** : `logs/scolaris.log`
- **Fichier d'erreurs** : `logs/errors.log`

### Types de Logs
- ✅ **Succès** : `logger.info()`
- ⚠️ **Avertissements** : `logger.warning()`
- ❌ **Erreurs** : `logger.error()`

## 🚀 Passage en Production

### Email
1. Changer `EMAIL_BACKEND` vers `smtp.EmailBackend`
2. Configurer les vraies valeurs SMTP
3. Utiliser des variables d'environnement pour les credentials

### SMS
1. Vérifier que les vraies credentials SMSVAS sont dans `.env`
2. Tester avec un vrai numéro de téléphone
3. Monitorer les logs pour détecter les échecs

## 📱 Configuration SMSVAS

### API Endpoint
```
https://smsvas.com/bulk/public/index.php/api/v1/sendsms
```

### Paramètres Requis
- `username` : Votre nom d'utilisateur SMSVAS
- `password` : Votre mot de passe SMSVAS
- `sender_id` : Identifiant de l'expéditeur
- `mobile` : Numéro de téléphone du destinataire
- `message` : Contenu du message

### Format du Numéro
- **Cameroun** : `+237612345678`
- **International** : `+[code_pays][numéro]`

## 🔒 Sécurité

### Variables Sensibles
- ✅ **SMS_USER** : Nom d'utilisateur API
- ✅ **SMS_PASSWORD** : Mot de passe API
- ✅ **EMAIL_HOST_PASSWORD** : Mot de passe SMTP

### Bonnes Pratiques
1. **Jamais** commiter le fichier `.env` dans Git
2. **Toujours** utiliser des variables d'environnement
3. **Limiter** l'accès aux credentials API
4. **Monitorer** l'utilisation des API

## 📞 Support

### En Cas de Problème
1. Vérifier les logs dans `logs/errors.log`
2. Tester avec `python test_notifications_env.py`
3. Vérifier la configuration dans `.env`
4. Tester la connectivité API SMSVAS

### Debug
- **Email** : Vérifier la console Django
- **SMS** : Vérifier les logs et la réponse API
- **Configuration** : Vérifier les variables d'environnement
