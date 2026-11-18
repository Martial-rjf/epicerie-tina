import os
import django
from decimal import Decimal
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from stocks.models import Ingredient, ProduitFini, CompositionProduit, MouvementStock, Fournisseur
from django.utils import timezone

print("🔄 Chargement des données de démonstration...")

# 1. Fournisseur
fournisseur, _ = Fournisseur.objects.get_or_create(
    nom="Boulangerie des Hauts",
    defaults={
        'contact': 'Jean Felice Martial',
        'telephone': '038 99 585 86',
        'email': 'randriamhajajeanfelicem@gmail.com',
        'adresse': 'Lot IV 123 Fianarantsoa'
    }
)
print(f"✅ Fournisseur : {fournisseur.nom}")

# 2. Ingrédients
ingredients_data = [
    ('Farine', 'kg', 50, 10, 2500),
    ('Sucre', 'kg', 20, 5, 4000),
    ('Beurre', 'kg', 15, 5, 12000),
    ('Sel', 'kg', 5, 2, 1500),
    ('Levure', 'kg', 3, 1, 8000),
    ('Œufs', 'pièce', 120, 30, 350),
    ('Lait', 'L', 10, 3, 2500),
    ('Chocolat', 'kg', 4, 1, 15000),
]

ingredients = {}
for nom, unite, qte, seuil, prix in ingredients_data:
    ing, created = Ingredient.objects.get_or_create(
        nom=nom,
        defaults={
            'unite': unite,
            'quantite_stock': Decimal(str(qte)),
            'seuil_alerte': Decimal(str(seuil)),
            'prix_unitaire': Decimal(str(prix)),
            'fournisseur': fournisseur
        }
    )
    ingredients[nom] = ing
    if created:
        print(f"✅ Ingrédient créé : {nom}")

# 3. Produits
produits_data = [
    ('Baguette', 4500),
    ('Croissant', 3500),
    ('Pain complet', 5500),
    ('Pain au chocolat', 6000),
    ('Brioche', 8000),
]

produits = {}
for nom, prix in produits_data:
    p, created = ProduitFini.objects.get_or_create(
        nom=nom,
        defaults={'prix_vente': Decimal(str(prix))}
    )
    produits[nom] = p
    if created:
        print(f"✅ Produit créé : {nom}")

# 4. Compositions
compositions = [
    ('Baguette', 'Farine', 0.250),
    ('Baguette', 'Sel', 0.005),
    ('Baguette', 'Levure', 0.010),
    ('Croissant', 'Farine', 0.150),
    ('Croissant', 'Beurre', 0.100),
    ('Croissant', 'Sucre', 0.030),
    ('Pain complet', 'Farine', 0.300),
    ('Pain complet', 'Sel', 0.005),
    ('Pain complet', 'Levure', 0.010),
    ('Pain au chocolat', 'Farine', 0.200),
    ('Pain au chocolat', 'Beurre', 0.080),
    ('Pain au chocolat', 'Chocolat', 0.020),
    ('Brioche', 'Farine', 0.250),
    ('Brioche', 'Beurre', 0.120),
    ('Brioche', 'Œufs', 2.000),
    ('Brioche', 'Sucre', 0.050),
]

for prod_nom, ing_nom, qte in compositions:
    try:
        prod = produits[prod_nom]
        ing = ingredients[ing_nom]
        comp, created = CompositionProduit.objects.get_or_create(
            produit=prod,
            ingredient=ing,
            defaults={'quantite_necessaire': Decimal(str(qte))}
        )
        if created:
            print(f"✅ Composition : {qte} {ing_nom} pour {prod_nom}")
    except KeyError:
        print(f"❌ Erreur : {prod_nom} ou {ing_nom} non trouvé")

# 5. Ventes des 7 derniers jours
print("🔄 Création des ventes de démonstration...")
aujourd_hui = timezone.now().date()

ventes_data = [
    (0, 'Baguette', 50),
    (0, 'Croissant', 30),
    (1, 'Baguette', 45),
    (1, 'Pain complet', 20),
    (2, 'Baguette', 40),
    (2, 'Croissant', 25),
    (3, 'Baguette', 35),
    (3, 'Pain au chocolat', 15),
    (4, 'Baguette', 30),
    (4, 'Croissant', 20),
    (4, 'Brioche', 10),
    (5, 'Baguette', 25),
    (5, 'Pain complet', 15),
    (6, 'Baguette', 20),
    (6, 'Croissant', 15),
]

for jours, prod_nom, qte in ventes_data:
    date_vente = aujourd_hui - timedelta(days=jours)
    try:
        prod = produits[prod_nom]
        for comp in prod.compositionproduit_set.all():
            besoin = comp.quantite_necessaire * qte
            MouvementStock.objects.create(
                ingredient=comp.ingredient,
                type_mouvement='SORTIE',
                quantite=besoin,
                date_mouvement=timezone.make_aware(datetime.combine(date_vente, datetime.min.time())),
                commentaire=f"Vente de {qte} {prod_nom}(s)"
            )
        print(f"✅ Vente de {qte} {prod_nom} le {date_vente}")
    except KeyError:
        print(f"❌ Produit {prod_nom} non trouvé")

print("\n🎉 Données de démonstration chargées avec succès !")
print("\n📊 Résumé :")
print(f"   - {len(ingredients)} ingrédients")
print(f"   - {len(produits)} produits")
print(f"   - {len(compositions)} compositions")
print(f"   - {len(ventes_data)} ventes enregistrées")