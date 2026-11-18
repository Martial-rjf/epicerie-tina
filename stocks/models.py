#============
#en tete du projet
from django.db import models
from decimal import Decimal

# ============================================================
# PRODUIT (anciennement Ingrédient)
# ============================================================
class Produit(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code_barre = models.CharField(max_length=50, blank=True, null=True, help_text="Code-barres du produit")
    categorie = models.CharField(max_length=50, blank=True, null=True, help_text="Catégorie du produit")
    unite = models.CharField(max_length=10, help_text="kg, L, pièce, boîte, etc.")
    quantite_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    seuil_alerte = models.DecimalField(max_digits=10, decimal_places=2, default=5)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    emplacement = models.CharField(max_length=50, blank=True, null=True, help_text="Rayon, étagère, local")
    
    # Relation avec le fournisseur
    fournisseur = models.ForeignKey(
        'Fournisseur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produits'
    )

    def __str__(self):
        return f"{self.nom} ({self.quantite_stock} {self.unite})"

    def est_en_alerte(self):
        return self.quantite_stock <= self.seuil_alerte

    def valeur_totale(self):
        return self.quantite_stock * self.prix_unitaire


# ============================================================
# ARTICLE DE VENTE (produit fini / article vendu)
# ============================================================
class ArticleVente(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2)
    # Relation avec la composition (pour les articles composés)
    # Pour une épicerie, on peut vendre des articles simples ou composés

    def __str__(self):
        return self.nom

# ============================================================
# COMPOSITION D'UN ARTICLE DE VENTE
# ============================================================
class CompositionArticle(models.Model):
    article = models.ForeignKey(ArticleVente, on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_necessaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Quantité nécessaire pour 1 unité de l'article"
    )

    class Meta:
        unique_together = ('article', 'produit')

    def __str__(self):
        return f"{self.article.nom} → {self.produit.nom} ({self.quantite_necessaire} {self.produit.unite})"


# ============================================================
# MOUVEMENT DE STOCK
# ============================================================
class MouvementStock(models.Model):
    TYPE_CHOICES = [
        ('ENTREE', 'Entrée / Réapprovisionnement'),
        ('SORTIE', 'Sortie / Vente'),
        ('PERTE', 'Perte / Casse'),
    ]

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    date_mouvement = models.DateTimeField(auto_now_add=True)
    emplacement = models.CharField(max_length=50, blank=True, null=True, help_text="Lieu du mouvement")
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_type_mouvement_display()} - {self.produit.nom}"


# ============================================================
# FOURNISSEUR
# ============================================================
class Fournisseur(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

# ============================================================
# COMMANDE
# ============================================================
class Commande(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('RECUE', 'Reçue'),
        ('ANNULEE', 'Annulée'),
        ('PARTIELLE', 'Partiellement reçue'),
    ]
    
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.CASCADE,
        related_name='commandes'
    )
    date_commande = models.DateTimeField(auto_now_add=True)
    date_reception = models.DateTimeField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Commande #{self.id} - {self.fournisseur.nom} ({self.get_statut_display()})"

# ============================================================
# LIGNE DE COMMANDE
# ============================================================
class LigneCommande(models.Model):
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name='lignes'
    )
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_commande = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_recue = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.produit.nom} - {self.quantite_commande} {self.produit.unite}"

    def sous_total(self):
        return self.quantite_commande * self.prix_unitaire