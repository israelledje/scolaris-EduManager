# Script d'attribution des groupes de matières

Ce script permet d'attribuer automatiquement des groupes (Groupe 1 ou Groupe 2) aux matières existantes dans la base de données.

## Problème résolu

Le modèle `Subject` dans `subjects/models.py` contient un champ `group` avec les choix :
- Groupe 1
- Groupe 2

Cependant, la modale de création/modification des matières ne permettait pas de sélectionner le groupe, et les matières existantes n'avaient pas de groupe attribué.

## Solutions implémentées

### 1. Correction du formulaire

**Fichier modifié :** `subjects/forms.py`

Le formulaire `SubjectForm` a été mis à jour pour inclure le champ `group` :

```python
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'group']  # Ajout du champ 'group'
        widgets = {
            # ... widgets avec styles Tailwind CSS
        }
```

### 2. Modale corrigée

La modale de création/modification utilise maintenant le template `subjects/partials/subject_form.html` qui affiche automatiquement tous les champs du formulaire, y compris le nouveau champ `group`.

### 3. Script d'attribution automatique

**Fichiers créés :**
- `scripts/assign_subject_groups.py` - Script standalone
- `subjects/management/commands/assign_subject_groups.py` - Commande Django

## Utilisation

### Option 1 : Commande Django (recommandée)

```bash
# Afficher la répartition actuelle
python manage.py assign_subject_groups --show-only

# Simulation (voir les modifications sans les appliquer)
python manage.py assign_subject_groups --dry-run

# Appliquer les modifications
python manage.py assign_subject_groups
```

### Option 2 : Script standalone

```bash
# Exécuter le script
python scripts/assign_subject_groups.py

# Ou via le shell Django
python manage.py shell < scripts/assign_subject_groups.py
```

## Logique d'attribution

### Groupe 1 (Matières générales)
- **Scientifiques :** Mathématiques, Physique, Chimie, SVT, Biologie, Sciences
- **Linguistiques :** Français, Anglais, Espagnol, Allemand, Italien, etc.
- **Littéraires :** Littérature, Philosophie, Histoire, Géographie
- **Arts :** Arts plastiques, Musique, Théâtre, Cinéma
- **Sport :** Éducation physique et sportive
- **Langues anciennes :** Latin, Grec

### Groupe 2 (Matières professionnelles/spécialisées)
- **Professionnelles :** Comptabilité, Gestion, Marketing, Vente
- **Techniques :** Maintenance, Mécanique, Électricité, Plomberie
- **Artisanales :** Menuiserie, Ébénisterie, Céramique
- **Services :** Cuisine, Restauration, Hôtellerie, Tourisme
- **Santé :** Soins infirmiers, Vétérinaire
- **Formation :** Formation professionnelle, Stage, Alternance

## Exemple de sortie

```
🔍 Analyse des matières existantes...
📚 15 matière(s) trouvée(s)
✅ Mathématiques: Groupe 1 → Groupe 1
✅ Français: Groupe 1 → Groupe 1
✅ Comptabilité: Groupe 1 → Groupe 2
✅ Physique: Groupe 1 → Groupe 1
⚠️  Informatique de gestion: groupe non déterminé automatiquement

============================================================
📊 RÉSUMÉ DE L'ATTRIBUTION DES GROUPES
============================================================
📚 Total des matières: 15
✅ Matières mises à jour: 1
   - Attribuées au Groupe 1: 0
   - Attribuées au Groupe 2: 1
ℹ️  Matières inchangées: 14

📝 DÉTAIL DES MODIFICATIONS:
   • Comptabilité: Groupe 1 → Groupe 2

🔍 VÉRIFICATION FINALE:
   - Matières dans le Groupe 1: 12
   - Matières dans le Groupe 2: 3

✨ Attribution des groupes terminée avec succès!
```

## Notes importantes

1. **Sécurité :** Le script utilise le mode `--dry-run` par défaut pour éviter les modifications accidentelles
2. **Flexibilité :** Les règles d'attribution peuvent être facilement modifiées dans le script
3. **Traçabilité :** Toutes les modifications sont loggées avec les anciens et nouveaux groupes
4. **Robustesse :** Le script gère les cas où aucune règle ne correspond à une matière

## Personnalisation

Pour ajouter de nouvelles règles d'attribution, modifiez les dictionnaires `GROUP_1_SUBJECTS` et `GROUP_2_SUBJECTS` dans le script.

Exemple :
```python
GROUP_1_SUBJECTS = {
    # ... mots-clés existants ...
    'nouvelle_matiere', 'autre_matiere',
}
```
