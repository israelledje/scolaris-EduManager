#!/usr/bin/env python3
"""
Script pour construire le CSS Tailwind en production
Usage: python build_css.py
"""
import subprocess
import sys
import os

def build_css():
    """Construit le CSS Tailwind optimisé pour la production"""
    try:
        # Vérifier si Node.js et npm sont installés
        subprocess.run(['node', '--version'], check=True, capture_output=True)
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
        
        print("🔧 Installation des dépendances npm...")
        subprocess.run(['npm', 'install'], check=True)
        
        print("🎨 Construction du CSS Tailwind...")
        subprocess.run(['npm', 'run', 'build:css'], check=True)
        
        print("✅ CSS construit avec succès!")
        print("📁 Fichier généré: static/src/dist/styles.css")
        
        # Vérifier que le fichier existe
        css_path = "static/src/dist/styles.css"
        if os.path.exists(css_path):
            size = os.path.getsize(css_path)
            print(f"📊 Taille du fichier CSS: {size / 1024:.1f} KB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la construction du CSS: {e}")
        return False
    except FileNotFoundError:
        print("❌ Node.js ou npm n'est pas installé")
        print("🔗 Installez Node.js depuis: https://nodejs.org/")
        return False

if __name__ == "__main__":
    success = build_css()
    sys.exit(0 if success else 1)
