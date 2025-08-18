# 📊 Application Finances - Scolaris

## 🎯 Description

L'application **Finances** de Scolaris gère l'ensemble des aspects financiers d'un établissement scolaire, incluant les frais de scolarité, les paiements, les remises, les moratoires et les rapports financiers.

## 🚀 Fonctionnalités Principales

### 📋 Structures de Frais
- **Création** : Définition des frais d'inscription et de scolarité par classe
- **Modification** : Mise à jour des montants et paramètres
- **Suppression** : Avec vérification des paiements associés
- **Tranches automatiques** : Division automatique en tranches de paiement

### 💰 Gestion des Paiements
- **Enregistrement individuel** : Paiement par étudiant et tranche
- **Paiements en lot** : Création multiple pour une classe
- **Impression de reçus** : Template professionnel avec logo et signature
- **Modes de paiement** : Espèces, Chèque, Mobile Money, Virement
- **Génération automatique** : Numéros de reçus uniques

### 🎁 Remises et Bourses
- **Attribution de remises** : Par étudiant et tranche
- **Gestion des bourses** : Montants et motifs
- **Modification et suppression** : Avec historique

### ⏰ Moratoires
- **Demande de moratoire** : Par étudiant et tranche
- **Approbation administrative** : Workflow de validation
- **Nouvelles dates d'échéance** : Report automatique

### 💸 Remboursements
- **Gestion des remboursements** : Annulation de paiements
- **Motifs et montants** : Traçabilité complète

### 📝 Frais Annexes
- **Frais supplémentaires** : Examens, uniformes, activités
- **Application par classe ou étudiant** : Flexibilité maximale

### 📊 Tableau de Bord et Rapports
- **Dashboard financier** : Statistiques en temps réel
- **Graphiques** : Paiements par mode et par mois
- **Statut financier étudiant** : Vue détaillée par étudiant

## 🏗️ Architecture

### Modèles de Données

```python
# Structures de frais
FeeStructure          # Structure de frais par classe et année
FeeTranche           # Tranches de paiement

# Paiements
TranchePayment       # Paiements effectifs
PaymentRefund        # Remboursements

# Remises et moratoires
FeeDiscount          # Remises et bourses
Moratorium           # Demandes de moratoire

# Frais annexes
ExtraFee             # Frais supplémentaires
```

### Relations Principales

```
School → FeeStructure → FeeTranche → TranchePayment
Student → TranchePayment, FeeDiscount, Moratorium
User → (toutes les opérations avec audit)
```

## 🔐 Sécurité et Permissions

### Rôles et Permissions

| Rôle | Permissions |
|------|-------------|
| **ADMIN** | Toutes les permissions |
| **DIRECTION** | Gestion complète (sauf suppression) |
| **SURVEILLANCE** | Enregistrement des paiements, consultation |
| **PROFESSEUR** | Consultation uniquement |
| **PARENT** | Consultation + demande de moratoire |
| **ELEVE** | Consultation uniquement |

### Audit et Traçabilité

- ✅ **Logging complet** : Toutes les opérations sont enregistrées
- ✅ **Messages de succès/échec** : Feedback utilisateur
- ✅ **Enregistrement des utilisateurs** : Qui fait quoi
- ✅ **Validation des données** : Contrôles de cohérence
- ✅ **Transactions atomiques** : Intégrité des données

## 🛠️ Installation et Configuration

### 1. Migrations

```bash
python manage.py makemigrations finances
python manage.py migrate
```

### 2. Permissions

```bash
python manage.py shell
```

```python
from finances.permissions import assign_finance_permissions_to_user
from authentication.models import User

# Assigner les permissions à un utilisateur
user = User.objects.get(username='admin')
assign_finance_permissions_to_user(user, 'ADMIN')
```

### 3. URLs

Les URLs sont automatiquement incluses dans `scolaris/urls.py` :

```python
path('finances/', include(('finances.urls', 'finances'), namespace='finances')),
```

## 📱 Interface Utilisateur

### Templates Principaux

- `financial_dashboard.html` - Tableau de bord principal
- `fee_structure_list.html` - Liste des structures de frais
- `payment_list.html` - Liste des paiements
- `payment_form.html` - Formulaire de paiement
- `payment_receipt.html` - Template de reçu imprimable

### Fonctionnalités UI

- ✅ **Responsive design** : Compatible mobile/desktop
- ✅ **Formulaires intelligents** : Calculs automatiques
- ✅ **Recherche et filtres** : Navigation facilitée
- ✅ **Pagination** : Gestion des grandes listes
- ✅ **Actions rapides** : Accès direct aux fonctions principales

## 🔧 API et Intégrations

### Vues AJAX

```python
# Récupérer les tranches d'une classe
GET /finances/ajax/tranches-for-class/?class_id=1

# Récupérer les étudiants d'une classe
GET /finances/ajax/students-for-class/?class_id=1
```

### Endpoints Principaux

```python
# Dashboard et rapports
finances/                           # Tableau de bord
finances/student/<id>/status/       # Statut financier étudiant

# Structures de frais
finances/fee-structures/            # Liste
finances/fee-structures/create/     # Création
finances/fee-structures/<id>/       # Détails
finances/fee-structures/<id>/update/ # Modification
finances/fee-structures/<id>/delete/ # Suppression

# Paiements
finances/payments/                  # Liste
finances/payments/create/           # Création
finances/payments/bulk/             # Paiements en lot
finances/payments/<id>/             # Détails
finances/payments/<id>/receipt/     # Impression reçu

# Autres modules
finances/discounts/                 # Gestion remises
finances/moratoriums/               # Gestion moratoires
finances/refunds/                   # Gestion remboursements
finances/extra-fees/                # Frais annexes
```

## 🧪 Tests

### Exécution des Tests

```bash
python manage.py test finances
```

### Couverture des Tests

- ✅ **Tests unitaires** : Modèles, formulaires, vues
- ✅ **Tests d'intégration** : Workflows complets
- ✅ **Tests de permissions** : Vérification des accès
- ✅ **Tests de validation** : Contrôles de données

## 📈 Optimisations

### Requêtes Optimisées

- ✅ **select_related** : Réduction des requêtes pour les relations ForeignKey
- ✅ **prefetch_related** : Optimisation des requêtes ManyToMany
- ✅ **aggregate** : Calculs optimisés avec une seule requête
- ✅ **Pagination** : Gestion efficace des grandes listes

### Performance

- ✅ **Cache des requêtes** : Réduction des accès base de données
- ✅ **Indexation** : Optimisation des recherches
- ✅ **Lazy loading** : Chargement à la demande
- ✅ **Compression** : Réduction de la bande passante

## 🐛 Dépannage

### Problèmes Courants

1. **Erreur de permission**
   ```python
   # Vérifier les permissions
   from finances.permissions import check_finance_permission
   check_finance_permission(user, 'view_financial_dashboard')
   ```

2. **Erreur de validation**
   ```python
   # Vérifier les données du formulaire
   form = FeeStructureForm(data=request.POST)
   if not form.is_valid():
       print(form.errors)
   ```

3. **Erreur de transaction**
   ```python
   # Utiliser des transactions atomiques
   from django.db import transaction
   with transaction.atomic():
       # Opérations critiques
   ```

### Logs et Debug

```python
import logging
logger = logging.getLogger(__name__)

# Ajouter des logs
logger.info("Opération réussie")
logger.error("Erreur détectée")
logger.debug("Informations de debug")
```

## 🔄 Maintenance

### Sauvegarde

```bash
# Sauvegarde de la base de données
python manage.py dumpdata finances > finances_backup.json

# Restauration
python manage.py loaddata finances_backup.json
```

### Nettoyage

```bash
# Supprimer les anciens fichiers
python manage.py cleanup_old_files

# Optimiser la base de données
python manage.py optimize_database
```

## 📞 Support

Pour toute question ou problème :

1. **Documentation** : Consulter ce README
2. **Logs** : Vérifier les logs Django
3. **Tests** : Exécuter les tests unitaires
4. **Permissions** : Vérifier les droits utilisateur

## 🚀 Roadmap

### Versions Futures

- [ ] **Export PDF** : Rapports financiers en PDF
- [ ] **Notifications** : Alertes automatiques
- [ ] **API REST** : Interface programmatique
- [ ] **Intégration bancaire** : Paiements en ligne
- [ ] **Analytics avancés** : Prédictions et tendances

---

**Développé avec ❤️ pour Scolaris** 