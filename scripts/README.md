# Scripts de Population des Données Scolaires

Ce dossier contient les scripts pour peupler automatiquement votre base de données avec des données scolaires complètes et réalistes pour le système éducatif camerounais.

## 📁 Fichiers Disponibles

### 🎯 Scripts Principaux

1. **`populate_school_data.py`** - Script principal de population
2. **`run_populate.py`** - Script d'exécution rapide avec confirmation
3. **`verify_curriculum.py`** - Script de vérification du curriculum

### 📚 Commande Django

4. **`../school/management/commands/populate_school_data.py`** - Commande Django

## 🚀 Utilisation

### Méthode 1 : Commande Django (Recommandée)
```bash
cd scolaris
python manage.py populate_school_data --confirm
```

### Méthode 2 : Script d'exécution rapide
```bash
cd scolaris
python scripts/run_populate.py
```

### Méthode 3 : Script direct
```bash
cd scolaris
python scripts/populate_school_data.py
```

### Méthode 4 : Via Django shell
```bash
cd scolaris
python manage.py shell < scripts/populate_school_data.py
```

## 🔍 Vérification du Curriculum

Pour vérifier que toutes les matières sont correctement assignées :

```bash
cd scolaris
python scripts/verify_curriculum.py
```

## 📊 Données Générées

### 🏫 Classes
- **Collège :** 6e M1/M2, 5e M1/M2, 4e A1/E1, 3e E1/E1
- **Lycée :** 2nde/1ère/Tle A (Littéraire), C (Scientifique), TI (Technologie Informatique)
- **Total :** 14 classes

### 👨‍🎓 Élèves
- **20 à 40 élèves** par classe (nombre aléatoire)
- Noms et prénoms camerounais authentiques
- Âges appropriés selon les classes
- Matricules uniques au format `STU{année}{numéro}`

### 📚 Matières Complètes (Programme Officiel)

#### Matières Communes (Toutes Classes)
- Français (FR)
- Anglais (ANG) 
- Mathématiques (MATH)
- Histoire-Géographie (HG)
- Éducation Civique et Morale (ECM)
- Éducation Physique et Sportive (EPS)

#### Matières Collège (6e à 3e)
- Sciences et Vie de la Terre (SVT)
- Sciences Physiques (PC)
- Allemand (ALL)
- Espagnol (ESP)
- Arts Plastiques (AP)
- Musique (MUS)
- Technologie (TECH)
- Informatique de Base (INFO_BASE)
- Travaux Pratiques (TP)

#### Matières Lycée A (Littéraire)
- Philosophie (PHIL)
- Littérature (LIT)
- Latin (LAT)
- Grec (GREC)
- Sciences Économiques et Sociales (SES)

#### Matières Lycée C (Scientifique)
- Physique-Chimie (PC)
- Sciences de la Vie et de la Terre (SVT)
- Sciences de l'Ingénieur (SI)
- Informatique (INFO)

#### Matières TI (Technologie Informatique)
- Algorithmique et Programmation (ALGO)
- Base de Données (BDD)
- Réseaux Informatiques (RES)
- Systèmes d'Exploitation (SE)
- Développement Web (WEB)
- Architecture des Ordinateurs (ARCHI)
- Analyse et Conception (UML)
- Électronique (ELEC)

### 👨‍🏫 Enseignants
- **45 enseignants** spécialisés
- Matières principales et secondaires
- Noms camerounais, coordonnées complètes
- Matricules au format `ENS{année}{numéro}`

### 📋 Affectations avec Coefficients
- **Coefficients conformes** au système camerounais
- **Heures par semaine** réalistes
- Professeurs titulaires assignés
- Enseignants qualifiés pour leurs matières

### 📖 Programmes Pédagogiques
- Programmes par matière et classe
- Unités d'apprentissage (3-6 par programme)
- Objectifs et compétences définis

### ⏰ Créneaux Horaires
- Emploi du temps de base (Lundi-Vendredi)
- 6 créneaux par jour
- Affectation enseignant/matière/classe

## ⚠️ Prérequis

1. **École configurée** : Une école doit exister dans la base de données
2. **Année scolaire active** : Une année scolaire avec statut 'EN_COURS'
3. **Utilisateur admin** : Pour les métadonnées de création

## 🛡️ Sécurité

- **Transaction atomique** : Tout ou rien, pas de données partielles
- **Gestion des doublons** : Vérification avant création
- **Validation des données** : Contraintes d'intégrité respectées

## 📈 Résultats Attendus

Après exécution complète :
- **14 classes** avec spécialités
- **~420-560 élèves** (selon randomisation)
- **45 enseignants** qualifiés
- **~35 matières** avec codes
- **Programmes pédagogiques** complets
- **Emplois du temps** structurés

## 🐛 Dépannage

### Erreur "Aucune école trouvée"
```bash
python manage.py shell
>>> from school.models import School
>>> School.objects.all()
```

### Erreur "Aucune année scolaire active"
```bash
python manage.py shell
>>> from school.models import SchoolYear
>>> SchoolYear.objects.filter(statut='EN_COURS')
```

### Vérifier les données créées
```bash
python scripts/verify_curriculum.py
```

## 📞 Support

En cas de problème, vérifiez :
1. La configuration Django
2. Les migrations appliquées
3. Les prérequis (école/année)
4. Les logs d'erreur pour plus de détails
