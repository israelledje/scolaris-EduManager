#!/usr/bin/env python
"""
Script pour supprimer tous les bulletins de la base de données
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from notes.models import Bulletin, BulletinLine
from school.models import SchoolYear

def delete_all_bulletins():
    """Supprime tous les bulletins de la base de données"""
    print("🗑️  Suppression de tous les bulletins")
    print("=" * 50)
    
    # Récupérer l'année scolaire en cours
    year = SchoolYear.objects.filter(statut='EN_COURS').first()
    if not year:
        print("❌ Aucune année scolaire en cours trouvée")
        return
    
    print(f"📅 Année scolaire: {year.annee}")
    
    # Compter les bulletins existants
    total_bulletins = Bulletin.objects.count()
    total_lines = BulletinLine.objects.count()
    
    print(f"📊 Statistiques actuelles:")
    print(f"   - Total bulletins: {total_bulletins}")
    print(f"   - Total lignes de bulletins: {total_lines}")
    
    if total_bulletins == 0:
        print("✅ Aucun bulletin à supprimer")
        return
    
    # Demander confirmation
    print(f"\n⚠️  ATTENTION: Vous êtes sur le point de supprimer {total_bulletins} bulletins et {total_lines} lignes de bulletins!")
    print("Cette action est irréversible.")
    
    confirmation = input("\nVoulez-vous continuer? (oui/non): ").lower().strip()
    
    if confirmation not in ['oui', 'o', 'yes', 'y']:
        print("❌ Suppression annulée")
        return
    
    try:
        # Supprimer d'abord les lignes de bulletins
        print("\n🗑️  Suppression des lignes de bulletins...")
        deleted_lines = BulletinLine.objects.all().delete()
        print(f"✅ {deleted_lines[0]} lignes de bulletins supprimées")
        
        # Puis supprimer les bulletins
        print("🗑️  Suppression des bulletins...")
        deleted_bulletins = Bulletin.objects.all().delete()
        print(f"✅ {deleted_bulletins[0]} bulletins supprimés")
        
        # Vérification finale
        remaining_bulletins = Bulletin.objects.count()
        remaining_lines = BulletinLine.objects.count()
        
        print(f"\n📊 Vérification finale:")
        print(f"   - Bulletins restants: {remaining_bulletins}")
        print(f"   - Lignes restantes: {remaining_lines}")
        
        if remaining_bulletins == 0 and remaining_lines == 0:
            print("🎉 Suppression terminée avec succès!")
        else:
            print("⚠️  Il reste encore des bulletins ou lignes")
    
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        import traceback
        traceback.print_exc()

def delete_bulletins_by_year():
    """Supprime les bulletins pour une année scolaire spécifique"""
    print("🗑️  Suppression des bulletins par année scolaire")
    print("=" * 50)
    
    # Lister les années scolaires disponibles
    years = SchoolYear.objects.all().order_by('-annee')
    
    if not years.exists():
        print("❌ Aucune année scolaire trouvée")
        return
    
    print("📅 Années scolaires disponibles:")
    for i, year in enumerate(years, 1):
        print(f"   {i}. {year.annee} ({year.statut})")
    
    try:
        choice = int(input("\nChoisissez le numéro de l'année scolaire: ")) - 1
        if choice < 0 or choice >= len(years):
            print("❌ Choix invalide")
            return
        
        selected_year = years[choice]
        print(f"\n📅 Année sélectionnée: {selected_year.annee}")
        
        # Compter les bulletins pour cette année
        bulletins_count = Bulletin.objects.filter(trimester__year=selected_year).count()
        lines_count = BulletinLine.objects.filter(bulletin__trimester__year=selected_year).count()
        
        print(f"📊 Bulletins trouvés pour {selected_year.annee}:")
        print(f"   - Bulletins: {bulletins_count}")
        print(f"   - Lignes: {lines_count}")
        
        if bulletins_count == 0:
            print("✅ Aucun bulletin à supprimer pour cette année")
            return
        
        # Demander confirmation
        print(f"\n⚠️  ATTENTION: Vous êtes sur le point de supprimer {bulletins_count} bulletins pour l'année {selected_year.annee}!")
        print("Cette action est irréversible.")
        
        confirmation = input("\nVoulez-vous continuer? (oui/non): ").lower().strip()
        
        if confirmation not in ['oui', 'o', 'yes', 'y']:
            print("❌ Suppression annulée")
            return
        
        # Supprimer les bulletins pour cette année
        print("\n🗑️  Suppression des bulletins...")
        deleted_bulletins = Bulletin.objects.filter(trimester__year=selected_year).delete()
        print(f"✅ {deleted_bulletins[0]} bulletins supprimés")
        
        print("🎉 Suppression terminée avec succès!")
    
    except ValueError:
        print("❌ Veuillez entrer un numéro valide")
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Menu principal"""
    print("🗑️  Script de suppression des bulletins")
    print("=" * 50)
    print("1. Supprimer TOUS les bulletins")
    print("2. Supprimer les bulletins par année scolaire")
    print("3. Quitter")
    
    choice = input("\nChoisissez une option (1-3): ").strip()
    
    if choice == '1':
        delete_all_bulletins()
    elif choice == '2':
        delete_bulletins_by_year()
    elif choice == '3':
        print("👋 Au revoir!")
    else:
        print("❌ Option invalide")

if __name__ == "__main__":
    main()
