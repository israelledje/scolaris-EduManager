#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scolaris.settings')
django.setup()

from finances.models import ExtraFee, ExtraFeeType
from school.models import CurrentSchoolYear
from classes.models import SchoolClass
from django.contrib.auth.models import User

print("=== CRÉATION D'UN FRAIS ANNEXE DE TEST ===")
print()

# 1. Vérifier l'année scolaire actuelle
current_year = CurrentSchoolYear.objects.first()
if not current_year:
    print("❌ Aucune année scolaire actuelle définie")
    exit(1)

print(f"✅ Année scolaire actuelle : {current_year.year.annee}")

# 2. Vérifier les types de frais
fee_types = ExtraFeeType.objects.all()
if not fee_types:
    print("❌ Aucun type de frais annexe créé")
    exit(1)

print(f"✅ Types de frais disponibles : {fee_types.count()}")

# 3. Vérifier les classes
classes = SchoolClass.objects.filter(year=current_year.year)
if not classes:
    print("❌ Aucune classe trouvée pour cette année")
    exit(1)

print(f"✅ Classes disponibles : {classes.count()}")

# 4. Créer un frais annexe de test
try:
    # Utiliser le premier type de frais disponible
    fee_type = fee_types.first()
    
    # Créer le frais annexe
    extra_fee = ExtraFee.objects.create(
        name="Frais de transport scolaire",
        fee_type=fee_type,
        description="Transport scolaire quotidien pour tous les élèves",
        amount=15000.00,
        year=current_year.year,
        is_active=True,
        apply_to_all_classes=True,
        is_optional=False
    )
    
    # Ajouter quelques classes spécifiques
    extra_fee.classes.add(*classes[:3])  # Ajouter les 3 premières classes
    
    print(f"✅ Frais annexe créé avec succès : {extra_fee.name}")
    print(f"   Montant : {extra_fee.amount} FCFA")
    print(f"   Type : {extra_fee.fee_type.name}")
    print(f"   Classes : {extra_fee.classes.count()}")
    
except Exception as e:
    print(f"❌ Erreur lors de la création : {e}")
    import traceback
    traceback.print_exc()

print()
print("=== FIN DE LA CRÉATION ===")
