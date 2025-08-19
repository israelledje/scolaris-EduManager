#!/usr/bin/env python3
"""
Script de déploiement pour EduManager
Gère la compilation CSS et la collecte des fichiers statiques
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Exécute une commande et gère les erreurs"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erreur:")
        print(f"   Commande: {cmd}")
        print(f"   Code de sortie: {e.returncode}")
        if e.stdout:
            print(f"   Sortie: {e.stdout}")
        if e.stderr:
            print(f"   Erreur: {e.stderr}")
        return False

def check_files():
    """Vérifie que les fichiers critiques existent"""
    files_to_check = [
        "package.json",
        "tailwind.config.js",
        "static/src/input.css"
    ]
    
    print("🔍 Vérification des fichiers...")
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ Fichier manquant: {file_path}")
            return False
        else:
            print(f"✅ Trouvé: {file_path}")
    return True

def deploy():
    """Process de déploiement complet"""
    print("🚀 Début du déploiement EduManager")
    print("=" * 50)
    
    # 1. Vérification des fichiers
    if not check_files():
        print("❌ Vérification des fichiers échouée")
        return False
    
    # 2. Installation des dépendances npm
    if not run_command("npm install", "Installation des dépendances npm"):
        return False
    
    # 3. Compilation du CSS Tailwind
    if not run_command("npm run build:css", "Compilation du CSS Tailwind"):
        return False
    
    # 4. Vérification du fichier CSS généré
    css_path = "static/src/dist/styles.css"
    if os.path.exists(css_path):
        size = os.path.getsize(css_path) / 1024
        print(f"✅ CSS généré: {css_path} ({size:.1f} KB)")
    else:
        print(f"❌ CSS non généré: {css_path}")
        return False
    
    # 5. Collecte des fichiers statiques Django
    if not run_command("python manage.py collectstatic --noinput", "Collecte des fichiers statiques"):
        return False
    
    # 6. Vérification finale
    staticfiles_css = "staticfiles/src/dist/styles.css"
    if os.path.exists(staticfiles_css):
        size = os.path.getsize(staticfiles_css) / 1024
        print(f"✅ CSS dans staticfiles: {staticfiles_css} ({size:.1f} KB)")
    else:
        print(f"⚠️  CSS non trouvé dans staticfiles: {staticfiles_css}")
    
    print("=" * 50)
    print("🎉 Déploiement terminé avec succès!")
    print("📋 Résumé:")
    print("   • CSS Tailwind compilé")
    print("   • Fichiers statiques collectés")
    print("   • Prêt pour la production")
    
    return True

def clean():
    """Nettoie les fichiers temporaires"""
    print("🧹 Nettoyage des fichiers temporaires...")
    
    paths_to_clean = [
        "staticfiles",
        "static/src/dist/styles.css",
        "node_modules"
    ]
    
    for path in paths_to_clean:
        if os.path.exists(path):
            import shutil
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"🗑️  Dossier supprimé: {path}")
            else:
                os.remove(path)
                print(f"🗑️  Fichier supprimé: {path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Script de déploiement EduManager")
    parser.add_argument("--clean", action="store_true", help="Nettoyer avant déploiement")
    parser.add_argument("--only-css", action="store_true", help="Compiler seulement le CSS")
    
    args = parser.parse_args()
    
    if args.clean:
        clean()
    
    if args.only_css:
        # Compilation CSS seulement
        success = (check_files() and 
                  run_command("npm install", "Installation npm") and
                  run_command("npm run build:css", "Compilation CSS"))
    else:
        # Déploiement complet
        success = deploy()
    
    sys.exit(0 if success else 1)
