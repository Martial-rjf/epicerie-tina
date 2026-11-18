from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from stocks.models import Ingredient, ProduitFini, CompositionProduit, MouvementStock

class Command(BaseCommand):
    help = 'Crée les groupes et permissions pour l\'application'

    def handle(self, *args, **kwargs):
        # --- Créer les groupes ---
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        employee_group, _ = Group.objects.get_or_create(name='Employé')

        # --- Permissions pour les ingrédients ---
        ingredient_ct = ContentType.objects.get_for_model(Ingredient)
        ingredient_perms = Permission.objects.filter(content_type=ingredient_ct)

        # --- Permissions pour les produits ---
        produit_ct = ContentType.objects.get_for_model(ProduitFini)
        produit_perms = Permission.objects.filter(content_type=produit_ct)

        # --- Permissions pour les compositions ---
        composition_ct = ContentType.objects.get_for_model(CompositionProduit)
        composition_perms = Permission.objects.filter(content_type=composition_ct)

        # --- Permissions pour les mouvements ---
        mouvement_ct = ContentType.objects.get_for_model(MouvementStock)
        mouvement_perms = Permission.objects.filter(content_type=mouvement_ct)

        # --- Assigner les permissions ---
        # Admin : toutes les permissions
        admin_group.permissions.set(
            list(ingredient_perms) + 
            list(produit_perms) + 
            list(composition_perms) + 
            list(mouvement_perms)
        )

        # Manager : tout sauf supprimer
        manager_perms = []
        for perm in ingredient_perms:
            if 'delete' not in perm.codename:
                manager_perms.append(perm)
        for perm in produit_perms:
            if 'delete' not in perm.codename:
                manager_perms.append(perm)
        for perm in composition_perms:
            if 'delete' not in perm.codename:
                manager_perms.append(perm)
        for perm in mouvement_perms:
            if 'delete' not in perm.codename:
                manager_perms.append(perm)
        manager_group.permissions.set(manager_perms)

        # Employé : seulement consulter et ajouter des ventes
        employee_perms = []
        for perm in ingredient_perms:
            if 'view' in perm.codename:
                employee_perms.append(perm)
        for perm in produit_perms:
            if 'view' in perm.codename:
                employee_perms.append(perm)
        for perm in mouvement_perms:
            if 'add' in perm.codename or 'view' in perm.codename:
                employee_perms.append(perm)
        employee_group.permissions.set(employee_perms)

        self.stdout.write(self.style.SUCCESS('✅ Groupes et permissions créés avec succès !'))
