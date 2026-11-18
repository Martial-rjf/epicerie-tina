from django import forms
from .models import (
    Produit, ArticleVente, CompositionArticle, MouvementStock,
    Fournisseur, Commande, LigneCommande
)


# ============================================================
# FORMULAIRE POUR LES PRODUITS
# ============================================================
class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'code_barre', 'categorie', 'unite', 'quantite_stock', 
                  'seuil_alerte', 'prix_unitaire', 'emplacement', 'fournisseur']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Riz de Madagascar'}),
            'code_barre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1234567890123'}),
            'categorie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Alimentaire, Boisson'}),
            'unite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: kg, L, boîte'}),
            'quantite_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'emplacement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Rayon A, Étagère 2'}),
            'fournisseur': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom': 'Nom du produit',
            'code_barre': 'Code-barres',
            'categorie': 'Catégorie',
            'unite': 'Unité de mesure',
            'quantite_stock': 'Stock actuel',
            'seuil_alerte': 'Seuil d\'alerte',
            'prix_unitaire': 'Prix unitaire (Ar)',
            'emplacement': 'Emplacement / Localisation',
            'fournisseur': 'Fournisseur',
        }


# ============================================================
# FORMULAIRE POUR LES ARTICLES DE VENTE
# ============================================================
class ArticleVenteForm(forms.ModelForm):
    class Meta:
        model = ArticleVente
        fields = ['nom', 'prix_vente']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Panier de fruits'}),
            'prix_vente': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'nom': 'Nom de l\'article',
            'prix_vente': 'Prix de vente (Ar)',
        }


# ============================================================
# FORMULAIRE POUR LES COMPOSITIONS (Articles composés)
# ============================================================
class CompositionArticleForm(forms.ModelForm):
    class Meta:
        model = CompositionArticle
        fields = ['produit', 'quantite_necessaire']
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control'}),
            'quantite_necessaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'produit': 'Produit',
            'quantite_necessaire': 'Quantité nécessaire (par unité de l\'article)',
        }


# ============================================================
# FORMULAIRE POUR LES MOUVEMENTS
# ============================================================
class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['produit', 'type_mouvement', 'quantite', 'emplacement', 'commentaire']
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control'}),
            'type_mouvement': forms.Select(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'emplacement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Rayon A, Entrepôt'}),
            'commentaire': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Réapprovisionnement'}),
        }
        labels = {
            'produit': 'Produit',
            'type_mouvement': 'Type de mouvement',
            'quantite': 'Quantité',
            'emplacement': 'Emplacement',
            'commentaire': 'Commentaire / Description',
        }


# ============================================================
# FORMULAIRE POUR LES PERTES
# ============================================================
class PerteForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['produit', 'quantite', 'emplacement', 'commentaire']
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'emplacement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Étagère 3'}),
            'commentaire': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Produit périmé, casse'}),
        }
        labels = {
            'produit': 'Produit',
            'quantite': 'Quantité perdue',
            'emplacement': 'Emplacement',
            'commentaire': 'Motif de la perte',
        }


# ============================================================
# FORMULAIRE POUR LES FOURNISSEURS
# ============================================================
class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'contact', 'telephone', 'email', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'nom': 'Nom du fournisseur',
            'contact': 'Personne à contacter',
            'telephone': 'Téléphone',
            'email': 'Email',
            'adresse': 'Adresse',
        }

# ============================================================
# FORMULAIRE POUR LES COMMANDES
# ============================================================
class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['fournisseur', 'commentaire']
        widgets = {
            'fournisseur': forms.Select(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'fournisseur': 'Fournisseur',
            'commentaire': 'Commentaire',
        }