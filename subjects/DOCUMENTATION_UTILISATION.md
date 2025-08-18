# 📚 Guide d'Utilisation du Système Pédagogique SCOLARIS

## 🎯 **Vue d'ensemble**

Ce guide vous accompagne dans l'utilisation du système de gestion pédagogique SCOLARIS. Vous apprendrez à créer et gérer des programmes pédagogiques, des unités d'apprentissage, des leçons et à suivre la progression des élèves.

---

## 🚀 **Démarrage Rapide**

### **1. Accès au Système**
- **URL principale** : `http://127.0.0.1:8000/subjects/pedagogy/`
- **Administration** : `http://127.0.0.1:8000/admin/` → Section "Subjects"
- **Intégration classe** : Onglet "Programme Pédagogique" dans la vue de détail de classe

### **2. Première Utilisation**
1. **Connectez-vous** avec un compte administrateur
2. **Accédez au tableau de bord** pédagogique
3. **Créez votre premier programme** pour une matière/classe
4. **Définissez des unités** d'apprentissage
5. **Planifiez des leçons** dans l'emploi du temps

---

## 📋 **Gestion des Programmes Pédagogiques**

### **Création d'un Programme**

#### **Via l'Interface d'Administration**
1. Allez dans `Admin` → `Subjects` → `Programmes de matières`
2. Cliquez sur `Ajouter un programme de matière`
3. Remplissez les champs :
   - **Matière** : Sélectionnez la matière concernée
   - **Classe** : Choisissez la classe cible
   - **Année scolaire** : Sélectionnez l'année d'application
   - **Titre** : Donnez un titre descriptif au programme
   - **Description** : Décrivez les objectifs généraux
   - **Objectifs** : Listez les objectifs d'apprentissage
   - **Heures totales** : Définissez le volume horaire prévu
   - **Niveau de difficulté** : Choisissez entre Débutant, Intermédiaire, Avancé
4. Cliquez sur `Enregistrer`

#### **Via l'Interface Utilisateur**
1. Allez dans le tableau de bord pédagogique
2. Cliquez sur `Nouveau Programme`
3. Remplissez le formulaire et validez

### **Gestion des Programmes**

#### **Activation/Désactivation**
- **Activer** : Cochez "Programme actif" pour le rendre disponible
- **Désactiver** : Décochez pour le mettre en pause

#### **Approbation**
- **Demande d'approbation** : Créez le programme avec "Programme approuvé" décoché
- **Approbation** : Un administrateur peut cocher cette case après validation

#### **Modification et Suppression**
- **Modifier** : Cliquez sur le nom du programme dans la liste
- **Supprimer** : Utilisez le bouton de suppression (attention : irréversible)

---

## 🎓 **Gestion des Unités d'Apprentissage**

### **Création d'une Unité**

#### **Étapes de Création**
1. **Accédez au programme** parent
2. **Cliquez sur** "Ajouter une unité d'apprentissage"
3. **Remplissez les champs** :
   - **Titre** : Nom de l'unité (ex: "Les nombres entiers")
   - **Description** : Explication détaillée du contenu
   - **Heures estimées** : Temps prévu pour cette unité
   - **Ordre** : Position dans la progression (1, 2, 3...)
   - **Concepts clés** : Notions principales abordées
   - **Compétences développées** : Savoir-faire acquis
   - **Objectifs d'apprentissage** : Ce que l'élève doit maîtriser

#### **Gestion des Prérequis**
- **Sélectionnez** les unités qui doivent être terminées avant celle-ci
- **Vérifiez** que l'ordre logique est respecté
- **Utilisez** la fonction "Peut être commencée" pour vérifier la cohérence

### **Organisation des Unités**

#### **Ordre de Progression**
1. **Commencez par les bases** (ordre 1, 2, 3...)
2. **Respectez les prérequis** entre unités
3. **Vérifiez la cohérence** de la progression

#### **Statut des Unités**
- **Active** : L'unité est en cours d'enseignement
- **Inactive** : L'unité est temporairement suspendue

---

## 📖 **Gestion des Leçons**

### **Création d'une Leçon**

#### **Planification de Base**
1. **Sélectionnez l'unité** d'apprentissage parente
2. **Choisissez le créneau** horaire dans l'emploi du temps
3. **Assignez l'enseignant** responsable
4. **Définissez le titre** de la leçon

#### **Contenu Pédagogique**
- **Objectifs spécifiques** : Ce qui sera appris dans cette séance
- **Activités prévues** : Exercices et travaux pratiques
- **Matériel nécessaire** : Ressources et outils requis
- **Durée prévue** : Temps estimé pour la leçon

#### **Planification Temporelle**
- **Date prévue** : Quand la leçon doit avoir lieu
- **Créneau horaire** : Heure et durée dans l'emploi du temps
- **Flexibilité** : Possibilité de report ou modification

### **Suivi des Leçons**

#### **Statuts Possibles**
- **Planifiée** : Leçon programmée mais pas encore commencée
- **En cours** : Leçon actuellement en cours d'enseignement
- **Terminée** : Leçon achevée avec succès
- **Annulée** : Leçon supprimée ou annulée
- **Reportée** : Leçon déplacée à une date ultérieure

#### **Gestion des Statuts**
1. **Démarrer une leçon** : Cliquez sur "Commencer" quand la leçon débute
2. **Terminer une leçon** : Marquez comme "Terminée" à la fin
3. **Modifier le statut** : Utilisez les boutons d'action appropriés

---

## 👥 **Suivi de la Progression des Élèves**

### **Évaluation des Leçons**

#### **Niveaux d'Évaluation**
- **Compréhension** : Niveau 1 (Faible) à 5 (Excellent)
- **Participation** : Niveau 1 (Faible) à 5 (Excellent)
- **Devoirs** : Réalisés ou non + qualité (1-5)

#### **Saisie des Évaluations**
1. **Accédez à la leçon** concernée
2. **Cliquez sur** "Évaluer les élèves"
3. **Remplissez** pour chaque élève :
   - Niveau de compréhension
   - Niveau de participation
   - Réalisation des devoirs
   - Qualité du travail
   - Commentaires personnalisés

### **Analyse des Progrès**

#### **Indicateurs de Performance**
- **Score global** : Moyenne sur 10 (compréhension + participation + bonus devoirs)
- **Niveau de performance** : Excellent, Bon, Moyen, Faible
- **Besoins d'attention** : Élèves nécessitant un suivi particulier

#### **Suivi par Matière**
- **Progression globale** : Pourcentage de completion par matière
- **Évolution temporelle** : Amélioration ou difficultés persistantes
- **Comparaison** : Performance relative aux autres élèves

---

## 📊 **Tableaux de Bord et Rapports**

### **Tableau de Bord Principal**

#### **Statistiques Globales**
- **Nombre total** de matières, programmes, unités, leçons
- **Programmes actifs** avec leur progression
- **Leçons récentes** et leur statut

#### **Actions Rapides**
- **Créer** un nouveau programme
- **Ajouter** une unité d'apprentissage
- **Planifier** une nouvelle leçon
- **Accéder** à la liste des programmes

### **Vue par Classe**

#### **Intégration dans l'Interface Classe**
1. **Allez dans** la vue de détail d'une classe
2. **Cliquez sur** l'onglet "Programme Pédagogique"
3. **Visualisez** :
   - Statistiques de la classe
   - Progression par matière
   - Leçons récentes
   - Actions disponibles

#### **Navigation et Actions**
- **Tableau de bord** : Vue globale du système
- **Nouveau programme** : Création rapide
- **Détails** : Accès aux programmes existants

---

## 🔧 **Configuration et Personnalisation**

### **Paramètres du Système**

#### **Activation des Fonctionnalités**
- **Notifications** : Alertes automatiques pour les retards
- **Validation** : Processus d'approbation des programmes
- **Suivi** : Niveau de détail des évaluations

#### **Personnalisation des Évaluations**
- **Échelles** : Adaptation des niveaux (1-5, 1-10, etc.)
- **Critères** : Ajout de critères d'évaluation spécifiques
- **Pondération** : Ajustement des coefficients par critère

### **Gestion des Droits d'Accès**

#### **Rôles Utilisateurs**
- **Administrateurs** : Accès complet à tous les modules
- **Enseignants** : Gestion de leurs programmes et leçons
- **Coordinateurs** : Validation et approbation des programmes
- **Observateurs** : Consultation en lecture seule

#### **Permissions par Module**
- **Programmes** : Création, modification, suppression
- **Unités** : Gestion du contenu pédagogique
- **Leçons** : Planification et suivi
- **Évaluations** : Saisie et consultation

---

## 📱 **Utilisation Mobile et Responsive**

### **Interface Adaptative**

#### **Navigation Mobile**
- **Menu hamburger** : Accès aux différentes sections
- **Onglets** : Navigation tactile optimisée
- **Formulaires** : Saisie adaptée aux petits écrans

#### **Fonctionnalités Mobiles**
- **Saisie rapide** : Évaluation des élèves en classe
- **Consultation** : Suivi des programmes en déplacement
- **Notifications** : Alertes push pour les événements importants

---

## 🚨 **Dépannage et Support**

### **Problèmes Courants**

#### **Erreurs de Création**
- **Vérifiez** que tous les champs obligatoires sont remplis
- **Assurez-vous** que les relations entre modèles sont cohérentes
- **Contrôlez** que les dates et heures sont logiques

#### **Problèmes d'Affichage**
- **Actualisez** la page pour recharger les données
- **Vérifiez** que vous êtes connecté avec les bons droits
- **Contrôlez** que les données existent en base

#### **Erreurs de Sauvegarde**
- **Vérifiez** la connexion à la base de données
- **Contrôlez** que les contraintes de validation sont respectées
- **Assurez-vous** que les permissions sont suffisantes

### **Support et Aide**

#### **Documentation**
- **Ce guide** : Référence complète d'utilisation
- **Aide contextuelle** : Infobulles dans l'interface
- **Tutoriels vidéo** : Démonstrations pas à pas

#### **Contact Support**
- **Email** : support@scolaris.com
- **Chat** : Support en ligne intégré
- **Téléphone** : +237 XXX XXX XXX

---

## 📈 **Bonnes Pratiques**

### **Organisation Pédagogique**

#### **Planification des Programmes**
1. **Commencez par l'essentiel** : Matières fondamentales en premier
2. **Respectez la progression** : Logique d'apprentissage cohérente
3. **Adaptez au niveau** : Difficulté progressive et adaptée
4. **Prévoyez la flexibilité** : Marge pour les ajustements

#### **Gestion des Unités**
1. **Définissez clairement** les objectifs et prérequis
2. **Estimez réalistement** le temps nécessaire
3. **Prévoyez les alternatives** : Plans B en cas de difficultés
4. **Documentez** les choix pédagogiques

#### **Suivi des Leçons**
1. **Planifiez à l'avance** : Évitez l'improvisation
2. **Adaptez en temps réel** : Ajustez selon les réactions des élèves
3. **Évaluez régulièrement** : Suivi continu de la progression
4. **Communiquez** : Partagez les observations avec l'équipe

### **Optimisation du Système**

#### **Performance**
1. **Limitez** le nombre de programmes simultanés
2. **Archivez** les programmes terminés
3. **Optimisez** les requêtes de base de données
4. **Surveillez** l'utilisation des ressources

#### **Maintenance**
1. **Sauvegardez** régulièrement les données
2. **Mettez à jour** le système et les modules
3. **Vérifiez** l'intégrité des données
4. **Formez** les utilisateurs aux nouvelles fonctionnalités

---

## 🔮 **Évolutions Futures**

### **Fonctionnalités Prévues**

#### **Intelligence Artificielle**
- **Recommandations** automatiques de progression
- **Détection** des difficultés d'apprentissage
- **Adaptation** automatique des contenus
- **Prédiction** des résultats

#### **Analytics Avancés**
- **Tableaux de bord** personnalisés
- **Rapports** détaillés et exportables
- **Comparaisons** inter-classes et inter-établissements
- **Tendances** et analyses prédictives

#### **Intégrations**
- **LMS** (Learning Management Systems)
- **Outils** de création de contenu
- **Plateformes** d'évaluation en ligne
- **Systèmes** de communication parents-école

---

## 📝 **Conclusion**

Le système de gestion pédagogique SCOLARIS vous offre un outil complet et flexible pour organiser, planifier et suivre l'enseignement dans votre établissement. 

**Commencez petit, grandissez progressivement** :
1. **Créez un programme** pour une matière simple
2. **Testez** avec une classe pilote
3. **Étendez** progressivement à d'autres matières
4. **Formez** votre équipe aux bonnes pratiques
5. **Optimisez** en fonction de vos retours d'expérience

**N'hésitez pas à nous contacter** pour toute question ou suggestion d'amélioration. Nous sommes là pour vous accompagner dans la réussite de votre projet pédagogique !

---

**SCOLARIS** - Système de Gestion Scolaire Intégré  
**Version** : 1.0.0  
**Date** : Janvier 2024  
**Support** : support@scolaris.com
