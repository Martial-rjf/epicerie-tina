from django.contrib import admin
from .models import (
    Produit, ArticleVente, CompositionArticle, MouvementStock,
    Fournisseur, Commande, LigneCommande
)

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'unite', 'quantite_stock', 'seuil_alerte', 'prix_unitaire', 'emplacement', 'est_en_alerte')
    # list_filter ne peut pas contenir de méthode, on retire 'est_en_alerte'
    list_filter = ('categorie', 'fournisseur')  # ← on garde seulement les champs réels
    search_fields = ('nom', 'code_barre')

    def est_en_alerte(self, obj):
        return obj.est_en_alerte()
    est_en_alerte.boolean = True
    est_en_alerte.short_description = "Alerte"

# Le reste du code reste identique...

@admin.register(ArticleVente)
class ArticleVenteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix_vente')
    search_fields = ('nom',)

@admin.register(CompositionArticle)
class CompositionArticleAdmin(admin.ModelAdmin):
    list_display = ('article', 'produit', 'quantite_necessaire')
    list_filter = ('article', 'produit')

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('produit', 'type_mouvement', 'quantite', 'date_mouvement', 'emplacement')
    list_filter = ('type_mouvement', 'date_mouvement')
    search_fields = ('produit__nom', 'commentaire')

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact', 'telephone', 'email')
    search_fields = ('nom', 'contact')

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'fournisseur', 'date_commande', 'statut', 'montant_total')
    list_filter = ('statut', 'date_commande')

@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = ('commande', 'produit', 'quantite_commande', 'prix_unitaire')