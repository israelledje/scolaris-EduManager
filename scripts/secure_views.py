#!/usr/bin/env python3
"""
Script de sécurisation des vues Django
=====================================

Ce script ajoute automatiquement la protection @login_required 
à toutes les vues qui ne sont pas déjà protégées.

Usage:
    cd scolaris
    python scripts/secure_views.py
"""

import os
import re
import glob

# Liste des apps à sécuriser
APPS_TO_SECURE = [
    'dashboard', 'students', 'teachers', 'classes', 'subjects', 
    'notes', 'finances', 'documents', 'school', 'notifications'
]

def secure_view_file(file_path):
    """Sécurise un fichier views.py"""
    print(f"🔒 Sécurisation de {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si les imports de sécurité existent
    has_login_required = '@login_required' in content or 'LoginRequiredMixin' in content
    has_imports = 'from django.contrib.auth.decorators import login_required' in content
    has_mixin_import = 'from django.contrib.auth.mixins import LoginRequiredMixin' in content
    
    modified = False
    
    # Ajouter les imports nécessaires
    if not has_imports or not has_mixin_import:
        # Trouver la ligne d'import Django
        import_pattern = r'(from django\..*?import.*?\n)'
        imports = re.findall(import_pattern, content)
        
        if imports:
            # Ajouter les imports après les imports Django existants
            last_import = imports[-1]
            new_imports = ""
            
            if not has_imports:
                new_imports += "from django.contrib.auth.decorators import login_required\n"
            if not has_mixin_import:
                new_imports += "from django.contrib.auth.mixins import LoginRequiredMixin\n"
            
            if new_imports:
                content = content.replace(last_import, last_import + new_imports)
                modified = True
                print("  ✅ Imports de sécurité ajoutés")
    
    # Protéger les vues basées sur des fonctions
    function_pattern = r'^def (\w+_view|dashboard_view)\(request'
    functions = re.findall(function_pattern, content, re.MULTILINE)
    
    for func_name in functions:
        # Vérifier si la fonction n'est pas déjà protégée
        func_def_pattern = rf'(@login_required\s*\n)?def {func_name}\(request'
        if not re.search(rf'@login_required\s*\ndef {func_name}\(request', content):
            # Ajouter @login_required avant la fonction
            old_pattern = rf'^def {func_name}\(request'
            new_pattern = f'@login_required\ndef {func_name}(request'
            content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)
            modified = True
            print(f"  ✅ @login_required ajouté à {func_name}")
    
    # Protéger les vues basées sur des classes
    class_pattern = r'^class (\w+View\w*)\([^)]*\):'
    classes = re.findall(class_pattern, content, re.MULTILINE)
    
    for class_name in classes:
        # Vérifier si la classe n'hérite pas déjà de LoginRequiredMixin
        class_def_pattern = rf'class {class_name}\([^)]*LoginRequiredMixin[^)]*\):'
        if not re.search(class_def_pattern, content):
            # Ajouter LoginRequiredMixin comme première classe parente
            old_pattern = rf'^class {class_name}\(([^)]*)\):'
            
            def replace_class(match):
                parents = match.group(1).strip()
                if parents:
                    return f'class {class_name}(LoginRequiredMixin, {parents}):'
                else:
                    return f'class {class_name}(LoginRequiredMixin):'
            
            new_content = re.sub(old_pattern, replace_class, content, flags=re.MULTILINE)
            if new_content != content:
                content = new_content
                modified = True
                print(f"  ✅ LoginRequiredMixin ajouté à {class_name}")
    
    # Sauvegarder si modifié
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  💾 Fichier sauvegardé: {file_path}")
    else:
        print(f"  ℹ️ Aucune modification nécessaire")
    
    return modified

def main():
    """Fonction principale"""
    print("🔐 SÉCURISATION DES VUES DJANGO")
    print("=" * 50)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    total_modified = 0
    
    for app in APPS_TO_SECURE:
        views_file = os.path.join(base_dir, app, 'views.py')
        
        if os.path.exists(views_file):
            if secure_view_file(views_file):
                total_modified += 1
        else:
            print(f"⚠️  Fichier non trouvé: {views_file}")
    
    print("\n" + "=" * 50)
    print(f"✅ SÉCURISATION TERMINÉE")
    print(f"📁 {total_modified} fichiers modifiés")
    print(f"🔒 Toutes les vues sont maintenant protégées!")
    print("=" * 50)

if __name__ == "__main__":
    main()
