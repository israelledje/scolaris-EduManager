# 🎨 Gestion des Styles - EduManager

## 📋 Vue d'ensemble

Ce projet utilise **Tailwind CSS v4** pour les styles, avec un système de secours CSS personnalisé pour garantir le fonctionnement de la sidebar en toutes circonstances.

## 🛠️ Configuration

### Fichiers importants :
- `static/src/input.css` - Fichier source Tailwind
- `static/src/dist/styles.css` - Fichier CSS compilé (ne pas modifier directement)
- `tailwind.config.js` - Configuration Tailwind
- `package.json` - Scripts de build

## 🚀 Commands de développement

### Installation des dépendances
```bash
npm install
```

### Développement (watch mode)
```bash
npm run watch:css
```

### Build pour la production
```bash
npm run build:css
```

### Script Python automatisé
```bash
python build_css.py
```

## 🏗️ Architecture CSS

### 1. Tailwind CSS (Principal)
- Framework CSS utility-first
- Configuration personnalisée avec couleurs du thème
- Classes responsives automatiques

### 2. CSS de secours (Sidebar)
Le template `base.html` contient un CSS de secours qui garantit :
- ✅ Affichage correct de la sidebar sur desktop
- ✅ Fonctionnement du menu mobile
- ✅ Indépendance de Tailwind pour les fonctionnalités critiques

### Structure responsive :
```css
/* Mobile : sidebar cachée par défaut */
#sidebar {
    transform: translateX(-100%);
}

/* Desktop : sidebar toujours visible */
@media (min-width: 1024px) {
    #sidebar {
        transform: translateX(0) !important;
    }
}
```

## 🐛 Résolution de problèmes

### Sidebar ne s'affiche pas
1. Vérifier que `static/src/dist/styles.css` existe
2. Régénérer le CSS : `npm run build:css`
3. Le CSS de secours devrait quand même fonctionner

### Classes Tailwind manquantes
1. Ajouter les classes dans `tailwind.config.js` → `safelist`
2. Régénérer le CSS

### En production
- ❌ **Ne pas** utiliser le CDN Tailwind
- ✅ **Toujours** précompiler le CSS avec `npm run build:css`
- ✅ Utiliser `python manage.py collectstatic` après le build

## 📦 Déploiement

### Étapes recommandées :
1. `npm install`
2. `npm run build:css`
3. `python manage.py collectstatic`
4. Redémarrer le serveur

### Script automatisé :
```bash
python build_css.py && python manage.py collectstatic --noinput
```

## 🎯 Classes CSS critiques

### Sidebar
- `.sidebar-gradient` - Arrière-plan dégradé
- `.sidebar-link` - Liens de navigation
- `.mobile-sidebar` - Comportement mobile

### Layout
- `.main-content` - Conteneur principal
- `.glass-effect` - Effet de transparence

### Animations
- Toutes les animations sont définies dans `base.html`
- Indépendantes de Tailwind pour la compatibilité

## 🔧 Personnalisation

### Couleurs du thème :
Modifier `tailwind.config.js` → `theme.extend.colors`

### Animations :
Modifier `base.html` → `<style>` section

### Responsive breakpoints :
Par défaut : 1024px pour desktop, modifiable dans les media queries
