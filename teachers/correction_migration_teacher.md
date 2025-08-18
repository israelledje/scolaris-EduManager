# Procédure de migration vers le modèle centralisé TeachingAssignment

## 1. Création du modèle centralisé

Un nouveau modèle `TeachingAssignment` a été créé dans `teachers/models.py` pour centraliser toutes les relations entre enseignants, matières, classes et années scolaires, avec les champs suivants :

- `teacher` (ForeignKey vers Teacher)
- `subject` (ForeignKey vers Subject)
- `school_class` (ForeignKey vers SchoolClass)
- `year` (ForeignKey vers SchoolYear)
- `is_titulaire` (booléen, titulaire de la classe)
- `coefficient` (coefficient de la matière dans la classe)
- `hours_per_week` (nombre d'heures par semaine)

## 2. Migration de la base de données

- Générer la migration :
  ```bash
  python scolaris/manage.py makemigrations teachers
  ```
- Appliquer la migration :
  ```bash
  python scolaris/manage.py migrate teachers
  ```

## 3. Adaptation du code métier

### a. Affectation des enseignants

- Adapter les formulaires d'affectation (enseignant à une matière, à une classe, etc.) pour créer ou mettre à jour des objets `TeachingAssignment`.
- Pour chaque affectation, renseigner tous les champs nécessaires (enseignant, matière, classe, année, coefficient, heures, titulaire).

### b. Affichage des informations

- Pour afficher les matières d'un enseignant :
  ```python
  TeachingAssignment.objects.filter(teacher=mon_enseignant, year=annee)
  ```
- Pour afficher les enseignants d'une classe :
  ```python
  TeachingAssignment.objects.filter(school_class=ma_classe, year=annee)
  ```
- Pour afficher le titulaire d'une classe :
  ```python
  TeachingAssignment.objects.filter(school_class=ma_classe, is_titulaire=True, year=annee).first()
  ```

### c. Nettoyage des anciens champs

- Supprimer les champs et modèles redondants :
  - `main_teacher` dans `SchoolClass`
  - `main_class` dans `Teacher`
  - Le champ `teacher` dans `SubjectCoefficient`
  - Le ManyToMany `teachers` dans `Subject`
  - Les modèles d'assignation intermédiaires inutiles
- Adapter les migrations pour supprimer ces champs.

## 4. Tests et validation

- Vérifier que toutes les affectations et affichages fonctionnent avec le nouveau modèle.
- Mettre à jour les tests unitaires si besoin.

## 5. Documentation

- Documenter la nouvelle logique d'affectation dans le README ou la documentation technique du projet.

---

**Avantages de cette approche** :

- Centralisation de toutes les relations dans un seul modèle
- Requêtes plus simples et cohérentes
- Facilité d'évolution et de maintenance
