from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import re
import json

from .models import (
    Produit, ArticleVente, CompositionArticle, MouvementStock,
    Fournisseur, Commande, LigneCommande
)
from .forms import (
    ProduitForm, ArticleVenteForm, CompositionArticleForm, PerteForm,
    FournisseurForm, CommandeForm, MouvementStockForm
)
from .decorators import admin_required, manager_required, employee_required


# ============================================================
# 0. VITRINE PUBLIQUE (page d'accueil avant connexion)
# ============================================================
def vitrine(request):
    """Page d'accueil publique — accessible sans connexion."""
    return render(request, 'stocks/vitrine.html')


# ============================================================
# 1. ACCUEIL - TABLEAU DE BORD
# ============================================================
@login_required
def accueil(request):
    # --- Alertes de stock ---
    alertes = Produit.objects.filter(quantite_stock__lte=F('seuil_alerte')).order_by('quantite_stock')
    nb_alertes = alertes.count()

    # --- Stock Final (valeur actuelle du stock AU PRIX DE REVIENT) ---
    stock_final = Produit.objects.aggregate(
        total=Sum(F('quantite_stock') * F('prix_unitaire'))
    )['total'] or Decimal('0.00')

    aujourd_hui = timezone.now().date()
    hier = aujourd_hui - timedelta(days=1)

    # ========================================
    # VENTES DU JOUR
    # ========================================
    ventes_jour = MouvementStock.objects.filter(
        type_mouvement='SORTIE',
        commentaire__icontains='Vente',
        date_mouvement__date=aujourd_hui
    )

    total_ventes_valeur = Decimal('0.00')   # Chiffre d'affaires (prix de VENTE)
    total_ventes_cout = Decimal('0.00')     # Coût (prix de REVIENT)
    ventes_details = []

    for vente in ventes_jour:
        commentaire = vente.commentaire
        match = re.search(r'Vente de (\d+) (.+?)\(s\)', commentaire)
        cout = vente.quantite * vente.produit.prix_unitaire
        total_ventes_cout += cout

        if match:
            quantite_articles = int(match.group(1))
            nom_article = match.group(2)
            try:
                article = ArticleVente.objects.get(nom=nom_article)
                total_vente = quantite_articles * article.prix_vente
                total_ventes_valeur += total_vente
                ventes_details.append({
                    'nom': nom_article,
                    'quantite': quantite_articles,
                    'prix_unitaire': article.prix_vente,
                    'total': total_vente,
                })
            except ArticleVente.DoesNotExist:
                total_ventes_valeur += cout
        else:
            total_ventes_valeur += cout

    ventes_jour_quantite = sum(d['quantite'] for d in ventes_details)

    # ========================================
    # VENTES HIER
    # ========================================
    ventes_hier = MouvementStock.objects.filter(
        type_mouvement='SORTIE',
        commentaire__icontains='Vente',
        date_mouvement__date=hier
    )
    total_ventes_hier_valeur = Decimal('0.00')
    for vente in ventes_hier:
        total_ventes_hier_valeur += vente.quantite * vente.produit.prix_unitaire

    # ========================================
    # AJUSTEMENTS DU JOUR
    # ========================================
    pertes_jour = MouvementStock.objects.filter(
        type_mouvement='PERTE',
        date_mouvement__date=aujourd_hui
    )

    sorties_non_vente = MouvementStock.objects.filter(
        type_mouvement='SORTIE',
        date_mouvement__date=aujourd_hui
    ).exclude(commentaire__icontains='Vente')

    difference = Decimal('0.00')
    ajustements_details = []

    # Ajouter les PERTES
    for ajust in pertes_jour:
        valeur = ajust.quantite * ajust.produit.prix_unitaire
        difference += valeur
        ajustements_details.append({
            'produit': ajust.produit.nom,
            'quantite': ajust.quantite,
            'unite': ajust.produit.unite,
            'prix_unitaire': ajust.produit.prix_unitaire,
            'total': valeur,
            'motif': ajust.commentaire,
            'type': 'Perte',
            'date': ajust.date_mouvement,
        })

    # Ajouter les SORTIES non-vente
    for ajust in sorties_non_vente:
        valeur = ajust.quantite * ajust.produit.prix_unitaire
        difference += valeur
        ajustements_details.append({
            'produit': ajust.produit.nom,
            'quantite': ajust.quantite,
            'unite': ajust.produit.unite,
            'prix_unitaire': ajust.produit.prix_unitaire,
            'total': valeur,
            'motif': ajust.commentaire,
            'type': 'Sortie manuelle',
            'date': ajust.date_mouvement,
        })

    difference = Decimal(str(difference)).quantize(Decimal('0.01'))

    # ========================================
    # ENTRÉES DU JOUR (achats)
    # ========================================
    entrees_jour = MouvementStock.objects.filter(
        type_mouvement='ENTREE',
        date_mouvement__date=aujourd_hui
    )
    total_entrees_valeur = Decimal('0.00')
    for entree in entrees_jour:
        total_entrees_valeur += entree.quantite * entree.produit.prix_unitaire

    # ========================================
    # FORMULE DU STOCK INITIAL
    # Stock Initial = Stock Final − Entrées + Ventes(coût) + Ajustements
    # ========================================
    stock_initial = stock_final - total_entrees_valeur + total_ventes_cout + difference

    difference_pourcentage = (difference / total_ventes_valeur * 100) if total_ventes_valeur != 0 else 0

    # ========================================
    # VENTES DU MOIS
    # ========================================
    debut_mois = aujourd_hui.replace(day=1)
    ventes_mois_quantite = MouvementStock.objects.filter(
        type_mouvement='SORTIE',
        commentaire__icontains='Vente',
        date_mouvement__date__gte=debut_mois
    ).aggregate(total=Sum('quantite'))['total'] or 0

    # ========================================
    # GRAPHIQUE 7 JOURS
    # ========================================
    from django.db.models.functions import TruncDate
    sept_jours = aujourd_hui - timedelta(days=7)
    ventes_par_jour = MouvementStock.objects.filter(
        type_mouvement='SORTIE',
        commentaire__icontains='Vente',
        date_mouvement__date__gte=sept_jours
    ).annotate(jour=TruncDate('date_mouvement')).values('jour').annotate(total=Sum('quantite')).order_by('jour')

    labels = []
    data = []
    for v in ventes_par_jour:
        labels.append(v['jour'].strftime('%d/%m'))
        data.append(float(v['total']))

    if not labels:
        for i in range(7):
            day = aujourd_hui - timedelta(days=6 - i)
            labels.append(day.strftime('%d/%m'))
            data.append(0)

    # ========================================
    # CONTEXTE
    # ========================================
    context = {
        'nb_alertes': nb_alertes,
        'stock_initial': stock_initial,
        'stock_final': stock_final,
        'vente_details': ventes_details,
        'ventes_jour_valeur': total_ventes_valeur,
        'ventes_jour_quantite': ventes_jour_quantite,
        'ventes_mois_quantite': ventes_mois_quantite,
        'alertes': alertes,
        'labels': json.dumps(labels),
        'data': json.dumps(data),
        'difference': difference,
        'difference_pourcentage': difference_pourcentage,
        'total_entrees_valeur': total_entrees_valeur,
        'produits': Produit.objects.all().order_by('nom'),
        'ventes_details': ventes_details,
        'ventes_hier_valeur': total_ventes_hier_valeur,
        'ajustements_details': ajustements_details,
    }

    return render(request, 'stocks/accueil.html', context)


# ============================================================
# 1bis. DÉTAIL DES VENTES DU JOUR (page séparée)
# ============================================================
@login_required
def detail_ventes_jour(request):
    aujourd_hui = timezone.now().date()

    ventes_jour = MouvementStock.objects.filter(
        type_mouvement='SORTIE',
        commentaire__icontains='Vente',
        date_mouvement__date=aujourd_hui
    )

    total_ventes_valeur = Decimal('0.00')
    ventes_details = []

    for vente in ventes_jour:
        commentaire = vente.commentaire
        match = re.search(r'Vente de (\d+) (.+?)\(s\)', commentaire)
        if match:
            quantite_articles = int(match.group(1))
            nom_article = match.group(2)
            try:
                article = ArticleVente.objects.get(nom=nom_article)
                total_vente = quantite_articles * article.prix_vente
                total_ventes_valeur += total_vente
                ventes_details.append({
                    'nom': nom_article,
                    'quantite': quantite_articles,
                    'prix_unitaire': article.prix_vente,
                    'total': total_vente,
                })
            except ArticleVente.DoesNotExist:
                total_ventes_valeur += vente.quantite * vente.produit.prix_unitaire
        else:
            total_ventes_valeur += vente.quantite * vente.produit.prix_unitaire

    ventes_jour_quantite = sum(d['quantite'] for d in ventes_details)

    context = {
        'ventes_details': ventes_details,
        'ventes_jour_valeur': total_ventes_valeur,
        'ventes_jour_quantite': ventes_jour_quantite,
        'date_jour': aujourd_hui,
    }
    return render(request, 'stocks/detail_ventes_jour.html', context)


# ============================================================
# 2. GESTION DES PRODUITS
# ============================================================
@login_required
def gestion_produits(request):
    produits = Produit.objects.all().order_by('nom')

    if request.method == 'POST':
        produit_id = request.POST.get('produit_id')
        action = request.POST.get('action')
        quantite_str = request.POST.get('quantite')

        if produit_id and action and quantite_str:
            try:
                quantite = Decimal(quantite_str)
                if quantite <= 0:
                    messages.error(request, "La quantité doit être positive.")
                    return redirect('gestion_produits')

                produit = get_object_or_404(Produit, id=produit_id)

                if action == 'ENTREE':
                    produit.quantite_stock += quantite
                    messages.success(request, f"✅ Ajout de {quantite} {produit.unite} pour {produit.nom}.")
                elif action == 'SORTIE':
                    if produit.quantite_stock < quantite:
                        messages.error(request, f"❌ Stock insuffisant pour {produit.nom} !")
                        return redirect('gestion_produits')
                    produit.quantite_stock -= quantite
                    messages.success(request, f"✅ Retrait de {quantite} {produit.unite} pour {produit.nom}.")
                else:
                    messages.error(request, "Action invalide.")
                    return redirect('gestion_produits')

                produit.save()
                MouvementStock.objects.create(
                    produit=produit,
                    type_mouvement=action,
                    quantite=quantite,
                    commentaire="Mouvement depuis le tableau de bord"
                )

            except (ValueError, TypeError):
                messages.error(request, "Veuillez entrer un nombre valide.")

        return redirect('gestion_produits')

    context = {'produits': produits}
    return render(request, 'stocks/dashboard.html', context)


# ============================================================
# 3. AJOUTER UN PRODUIT
# ============================================================
@login_required
def ajouter_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Produit ajouté avec succès !")
            return redirect('gestion_produits')
    else:
        form = ProduitForm()

    return render(request, 'stocks/produit_form.html', {
        'form': form,
        'titre': '➕ Ajouter un produit',
        'bouton': 'Ajouter',
        'icone': 'plus-circle'
    })


# ============================================================
# 4. MODIFIER UN PRODUIT
# ============================================================
@login_required
def modifier_produit(request, id):
    produit = get_object_or_404(Produit, id=id)

    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Produit '{produit.nom}' modifié avec succès !")
            return redirect('gestion_produits')
    else:
        form = ProduitForm(instance=produit)

    return render(request, 'stocks/produit_form.html', {
        'form': form,
        'titre': '✏️ Modifier un produit',
        'bouton': 'Enregistrer',
        'icone': 'pencil-square'
    })


# ============================================================
# 5. SUPPRIMER UN PRODUIT
# ============================================================
@login_required
def supprimer_produit(request, id):
    produit = get_object_or_404(Produit, id=id)

    if request.method == 'POST':
        produit.delete()
        messages.success(request, f"🗑️ Produit '{produit.nom}' supprimé avec succès !")
        return redirect('gestion_produits')

    return render(request, 'stocks/produit_confirm_delete.html', {
        'produit': produit
    })


# ============================================================
# 6. LISTE DES ARTICLES DE VENTE
# ============================================================
@login_required
def liste_articles(request):
    articles = ArticleVente.objects.all().order_by('nom')
    return render(request, 'stocks/liste_articles.html', {
        'articles': articles,
    })


# ============================================================
# 7. AJOUTER UN ARTICLE DE VENTE
# ============================================================
@login_required
def ajouter_article(request):
    if request.method == 'POST':
        form = ArticleVenteForm(request.POST)
        if form.is_valid():
            article = form.save()
            messages.success(request, f"✅ Article '{article.nom}' ajouté avec succès !")
            return redirect('liste_articles')
    else:
        form = ArticleVenteForm()

    return render(request, 'stocks/article_form.html', {
        'form': form,
        'titre': '➕ Ajouter un article',
        'bouton': 'Ajouter',
        'icone': 'plus-circle'
    })


# ============================================================
# 8. MODIFIER UN ARTICLE DE VENTE
# ============================================================
@login_required
def modifier_article(request, id):
    article = get_object_or_404(ArticleVente, id=id)

    if request.method == 'POST':
        form = ArticleVenteForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ Article '{article.nom}' modifié avec succès !")
            return redirect('liste_articles')
    else:
        form = ArticleVenteForm(instance=article)

    return render(request, 'stocks/article_form.html', {
        'form': form,
        'titre': '✏️ Modifier un article',
        'bouton': 'Enregistrer',
        'icone': 'pencil-square'
    })


# ============================================================
# 9. SUPPRIMER UN ARTICLE DE VENTE
# ============================================================
@login_required
def supprimer_article(request, id):
    article = get_object_or_404(ArticleVente, id=id)

    if request.method == 'POST':
        article.delete()
        messages.success(request, f"🗑️ Article '{article.nom}' supprimé avec succès !")
        return redirect('liste_articles')

    return render(request, 'stocks/article_confirm_delete.html', {
        'article': article
    })


# ============================================================
# 10. AJOUTER UNE COMPOSITION
# ============================================================
@login_required
def ajouter_composition(request, article_id):
    article = get_object_or_404(ArticleVente, id=article_id)

    if request.method == 'POST':
        form = CompositionArticleForm(request.POST)
        if form.is_valid():
            produit = form.cleaned_data['produit']
            existing = CompositionArticle.objects.filter(article=article, produit=produit).first()
            if existing:
                messages.warning(request,
                                 f"⚠️ Le produit '{produit.nom}' est déjà dans la composition de '{article.nom}'. Utilisez la modification.")
                return redirect('liste_articles')

            composition = form.save(commit=False)
            composition.article = article
            composition.save()
            messages.success(request, f"✅ Produit ajouté à la composition de '{article.nom}' !")
            return redirect('liste_articles')
    else:
        form = CompositionArticleForm()

    return render(request, 'stocks/composition_form.html', {
        'form': form,
        'article': article,
        'titre': f'➕ Ajouter un produit à {article.nom}',
        'bouton': 'Ajouter',
        'icone': 'plus-circle'
    })


# ============================================================
# 11. MODIFIER UNE COMPOSITION
# ============================================================
@login_required
def modifier_composition(request, id):
    composition = get_object_or_404(CompositionArticle, id=id)

    if request.method == 'POST':
        form = CompositionArticleForm(request.POST, instance=composition)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Composition modifiée avec succès !")
            return redirect('liste_articles')
    else:
        form = CompositionArticleForm(instance=composition)

    return render(request, 'stocks/composition_form.html', {
        'form': form,
        'article': composition.article,
        'titre': '✏️ Modifier une composition',
        'bouton': 'Enregistrer',
        'icone': 'pencil-square'
    })


# ============================================================
# 12. SUPPRIMER UNE COMPOSITION
# ============================================================
@login_required
def supprimer_composition(request, id):
    composition = get_object_or_404(CompositionArticle, id=id)
    article_nom = composition.article.nom

    if request.method == 'POST':
        composition.delete()
        messages.success(request, f"🗑️ Produit retiré de la composition de '{article_nom}' !")
        return redirect('liste_articles')

    return render(request, 'stocks/composition_confirm_delete.html', {
        'composition': composition
    })


# ============================================================
# 13. VENTE D'UN ARTICLE
# ============================================================
@login_required
def vente_article(request, id):
    article = get_object_or_404(ArticleVente, id=id)
    compositions = article.compositionarticle_set.all()
    peut_vendre = True

    if not compositions:
        messages.error(request,
                       f"❌ L'article '{article.nom}' n'a pas de composition ! Ajoutez des produits à sa composition.")
        return redirect('liste_articles')

    if request.method == 'POST':
        quantite_str = request.POST.get('quantite')
        try:
            quantite = int(quantite_str)
            if quantite <= 0:
                messages.error(request, "La quantité doit être positive.")
                return redirect('liste_articles')

            for comp in compositions:
                besoin_total = comp.quantite_necessaire * quantite
                if comp.produit.quantite_stock < besoin_total:
                    messages.error(
                        request,
                        f"❌ Stock insuffisant pour '{comp.produit.nom}' ! "
                        f"(besoin: {besoin_total} {comp.produit.unite}, "
                        f"stock: {comp.produit.quantite_stock})"
                    )
                    peut_vendre = False

            if not peut_vendre:
                return redirect('liste_articles')

            for comp in compositions:
                besoin_total = comp.quantite_necessaire * quantite
                comp.produit.quantite_stock -= besoin_total
                comp.produit.save()

                MouvementStock.objects.create(
                    produit=comp.produit,
                    type_mouvement='SORTIE',
                    quantite=besoin_total,
                    commentaire=f"Vente de {quantite} {article.nom}(s)"
                )

            messages.success(request, f"✅ Vente de {quantite} {article.nom}(s) enregistrée avec succès !")
            return redirect('liste_articles')

        except (ValueError, TypeError):
            messages.error(request, "Veuillez entrer un nombre valide.")
            return redirect('liste_articles')

    return render(request, 'stocks/vente_article.html', {
        'article': article,
        'compositions': compositions,
    })


# ============================================================
# 14. FICHE DE STOCK
# ============================================================
@login_required
def fiche_stock(request):
    date_str = request.GET.get('date', timezone.now().date().isoformat())

    try:
        date_selectionnee = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        date_selectionnee = timezone.now().date()
        date_str = date_selectionnee.isoformat()

    debut_journee = datetime.combine(date_selectionnee, datetime.min.time())
    fin_journee = datetime.combine(date_selectionnee, datetime.max.time())

    produits = Produit.objects.all().order_by('nom')

    donnees = []
    total_stock_initial = Decimal('0.00')
    total_entrees = Decimal('0.00')
    total_ventes = Decimal('0.00')
    total_stock_final = Decimal('0.00')
    total_valeur = Decimal('0.00')

    for produit in produits:
        entrees_jour = MouvementStock.objects.filter(
            produit=produit,
            type_mouvement='ENTREE',
            date_mouvement__range=[debut_journee, fin_journee]
        ).aggregate(total=Sum('quantite'))['total'] or Decimal('0.00')

        ventes_jour = MouvementStock.objects.filter(
            produit=produit,
            type_mouvement='SORTIE',
            date_mouvement__range=[debut_journee, fin_journee]
        ).aggregate(total=Sum('quantite'))['total'] or Decimal('0.00')

        stock_initial = produit.quantite_stock - entrees_jour + ventes_jour
        stock_final = stock_initial + entrees_jour - ventes_jour
        valeur = stock_final * produit.prix_unitaire

        donnees.append({
            'produit': produit,
            'stock_initial': stock_initial,
            'entrees': entrees_jour,
            'ventes': ventes_jour,
            'stock_final': stock_final,
            'valeur': valeur,
        })

        total_stock_initial += stock_initial
        total_entrees += entrees_jour
        total_ventes += ventes_jour
        total_stock_final += stock_final
        total_valeur += valeur

    context = {
        'donnees': donnees,
        'date_selectionnee': date_selectionnee,
        'date_str': date_str,
        'total_stock_initial': total_stock_initial,
        'total_entrees': total_entrees,
        'total_ventes': total_ventes,
        'total_stock_final': total_stock_final,
        'total_valeur': total_valeur,
    }
    return render(request, 'stocks/fiche_stock.html', context)


# ============================================================
# 15. HISTORIQUE DES MOUVEMENTS
# ============================================================
@login_required
def historique_mouvements(request):
    mouvements = MouvementStock.objects.all().order_by('-date_mouvement')

    produit_id = request.GET.get('produit')
    type_mouvement = request.GET.get('type')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    if produit_id:
        mouvements = mouvements.filter(produit_id=produit_id)
    if type_mouvement:
        mouvements = mouvements.filter(type_mouvement=type_mouvement)
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            mouvements = mouvements.filter(date_mouvement__date__gte=date_debut_obj)
        except ValueError:
            pass
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            mouvements = mouvements.filter(date_mouvement__date__lte=date_fin_obj)
        except ValueError:
            pass

    produits = Produit.objects.all().order_by('nom')
    context = {
        'mouvements': mouvements,
        'produits': produits,
        'produit_id': produit_id,
        'type_mouvement': type_mouvement,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'TYPE_CHOICES': MouvementStock.TYPE_CHOICES,
    }
    return render(request, 'stocks/historique.html', context)


# ============================================================
# 16. EXPORT PDF
# ============================================================
@login_required
def export_pdf_fiche_stock(request):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    date_str = request.GET.get('date', timezone.now().date().isoformat())
    try:
        date_selectionnee = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        date_selectionnee = timezone.now().date()
        date_str = date_selectionnee.isoformat()

    debut_journee = datetime.combine(date_selectionnee, datetime.min.time())
    fin_journee = datetime.combine(date_selectionnee, datetime.max.time())
    produits = Produit.objects.all().order_by('nom')

    donnees = []
    total_stock_initial = Decimal('0.00')
    total_entrees = Decimal('0.00')
    total_ventes = Decimal('0.00')
    total_stock_final = Decimal('0.00')
    total_valeur = Decimal('0.00')

    for produit in produits:
        entrees_jour = MouvementStock.objects.filter(
            produit=produit,
            type_mouvement='ENTREE',
            date_mouvement__range=[debut_journee, fin_journee]
        ).aggregate(total=Sum('quantite'))['total'] or Decimal('0.00')

        ventes_jour = MouvementStock.objects.filter(
            produit=produit,
            type_mouvement='SORTIE',
            date_mouvement__range=[debut_journee, fin_journee]
        ).aggregate(total=Sum('quantite'))['total'] or Decimal('0.00')

        stock_initial = produit.quantite_stock - entrees_jour + ventes_jour
        stock_final = stock_initial + entrees_jour - ventes_jour
        valeur = stock_final * produit.prix_unitaire

        donnees.append([
            produit.nom,
            produit.unite,
            f"{stock_initial:.2f}",
            f"{entrees_jour:.2f}",
            f"{ventes_jour:.2f}",
            f"{stock_final:.2f}",
            f"{valeur:.2f}"
        ])

        total_stock_initial += stock_initial
        total_entrees += entrees_jour
        total_ventes += ventes_jour
        total_stock_final += stock_final
        total_valeur += valeur

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_stock_{date_str}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=20,
        textColor=colors.HexColor('#1e3c72')
    )
    elements.append(Paragraph("FICHE DE STOCK - ÉPICERIE TINA", title_style))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"Date : {date_selectionnee.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 15))

    table_data = [
        ['Produit', 'Unité', 'Stock Initial', 'Entrées', 'Ventes', 'Stock Final', 'Valeur (Ar)']
    ]
    table_data.extend(donnees)
    table_data.append([
        'TOTAUX', '',
        f"{total_stock_initial:.2f}",
        f"{total_entrees:.2f}",
        f"{total_ventes:.2f}",
        f"{total_stock_final:.2f}",
        f"{total_valeur:.2f}"
    ])

    table = Table(table_data, colWidths=[3 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#eaf2f8')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -2), 8),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(
        "Formule : Stock Initial + Entrées - Ventes = Stock Final",
        styles['Normal']
    ))
    elements.append(Paragraph(
        f"Valeur totale du stock : {total_valeur:.2f} Ar",
        ParagraphStyle('TotalVal', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold',
                       textColor=colors.HexColor('#2980b9'))
    ))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f"Généré le {timezone.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.grey)
    ))

    doc.build(elements)
    return response


# ============================================================
# 17. GESTION DES PERTES
# ============================================================
@login_required
@manager_required
def gestion_pertes(request):
    pertes = MouvementStock.objects.filter(type_mouvement='PERTE').order_by('-date_mouvement')

    if request.method == 'POST':
        form = PerteForm(request.POST)
        if form.is_valid():
            perte = form.save(commit=False)
            perte.type_mouvement = 'PERTE'
            perte.save()

            produit = perte.produit
            produit.quantite_stock -= perte.quantite
            produit.save()

            messages.success(request, f"✅ Perte enregistrée : {perte.quantite} {produit.unite} de {produit.nom}")
            return redirect('gestion_pertes')
    else:
        form = PerteForm()

    total_pertes = pertes.aggregate(total=Sum('quantite'))['total'] or Decimal('0.00')
    nb_pertes = pertes.count()

    context = {
        'pertes': pertes,
        'form': form,
        'total_pertes': total_pertes,
        'nb_pertes': nb_pertes,
    }
    return render(request, 'stocks/gestion_pertes.html', context)


# ============================================================
# 18. SUPPRIMER UNE PERTE
# ============================================================
@login_required
@admin_required
def supprimer_perte(request, id):
    perte = get_object_or_404(MouvementStock, id=id, type_mouvement='PERTE')

    if request.method == 'POST':
        produit = perte.produit
        produit.quantite_stock += perte.quantite
        produit.save()

        perte.delete()
        messages.success(request, f"🗑️ Perte supprimée, stock restauré pour {produit.nom}")
        return redirect('gestion_pertes')

    return render(request, 'stocks/perte_confirm_delete.html', {
        'perte': perte
    })


# ============================================================
# 19. GESTION DES FOURNISSEURS
# ============================================================
@login_required
@manager_required
def gestion_fournisseurs(request):
    fournisseurs = Fournisseur.objects.all().order_by('nom')

    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Fournisseur ajouté avec succès !")
            return redirect('gestion_fournisseurs')
    else:
        form = FournisseurForm()

    return render(request, 'stocks/gestion_fournisseurs.html', {
        'fournisseurs': fournisseurs,
        'form': form,
    })


# ============================================================
# 20. LISTE DES COMMANDES
# ============================================================
@login_required
@manager_required
def liste_commandes(request):
    commandes = Commande.objects.all().order_by('-date_commande')
    return render(request, 'stocks/liste_commandes.html', {
        'commandes': commandes,
    })


# ============================================================
# 21. CREER UNE COMMANDE
# ============================================================
@login_required
@manager_required
def creer_commande(request):
    produits_alerte = Produit.objects.filter(quantite_stock__lte=F('seuil_alerte')).order_by('nom')

    if request.method == 'POST':
        form = CommandeForm(request.POST)
        if form.is_valid():
            commande = form.save()

            for prod in produits_alerte:
                quantite_proposee = max(prod.seuil_alerte * 2 - prod.quantite_stock, 0)
                if quantite_proposee > 0:
                    LigneCommande.objects.create(
                        commande=commande,
                        produit=prod,
                        quantite_commande=quantite_proposee,
                        prix_unitaire=prod.prix_unitaire
                    )

            total = sum(l.sous_total() for l in commande.lignes.all())
            commande.montant_total = total
            commande.save()

            messages.success(request, f"✅ Commande #{commande.id} créée avec {commande.lignes.count()} lignes.")
            return redirect('detail_commande', id=commande.id)
    else:
        form = CommandeForm()
        fournisseurs_ids = Produit.objects.filter(quantite_stock__lte=F('seuil_alerte')).values_list('fournisseur_id',
                                                                                                     flat=True).distinct()
        if fournisseurs_ids:
            form.fields['fournisseur'].queryset = Fournisseur.objects.filter(id__in=fournisseurs_ids)

    context = {
        'form': form,
        'produits_alerte': produits_alerte,
    }
    return render(request, 'stocks/creer_commande.html', context)


# ============================================================
# 22. DETAIL D'UNE COMMANDE
# ============================================================
@login_required
@manager_required
def detail_commande(request, id):
    commande = get_object_or_404(Commande, id=id)
    lignes = commande.lignes.all()

    if request.method == 'POST' and request.POST.get('action') == 'receptionner':
        for ligne in lignes:
            ligne.produit.quantite_stock += ligne.quantite_commande
            ligne.produit.save()

            MouvementStock.objects.create(
                produit=ligne.produit,
                type_mouvement='ENTREE',
                quantite=ligne.quantite_commande,
                commentaire=f"Réception commande #{commande.id}"
            )

            ligne.quantite_recue = ligne.quantite_commande
            ligne.save()

        commande.statut = 'RECUE'
        commande.date_reception = timezone.now()
        commande.save()

        messages.success(request, f"✅ Commande #{commande.id} réceptionnée avec succès !")
        return redirect('detail_commande', id=commande.id)

    return render(request, 'stocks/detail_commande.html', {
        'commande': commande,
        'lignes': lignes,
    })


# ============================================================
# 23. SUPPRIMER UNE COMMANDE
# ============================================================
@login_required
@admin_required
def supprimer_commande(request, id):
    commande = get_object_or_404(Commande, id=id)
    if request.method == 'POST':
        commande.delete()
        messages.success(request, "🗑️ Commande supprimée.")
        return redirect('liste_commandes')
    return render(request, 'stocks/commande_confirm_delete.html', {'commande': commande})


# ============================================================
# 24. HISTORIQUE DE L'ÉPICERIE
# ============================================================
@login_required
def historique_boulangerie(request):
    mouvements = MouvementStock.objects.all().order_by('-date_mouvement')

    type_mouvement = request.GET.get('type')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    produit_id = request.GET.get('produit')

    if type_mouvement:
        mouvements = mouvements.filter(type_mouvement=type_mouvement)
    if date_debut:
        try:
            mouvements = mouvements.filter(date_mouvement__date__gte=datetime.strptime(date_debut, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_fin:
        try:
            mouvements = mouvements.filter(date_mouvement__date__lte=datetime.strptime(date_fin, '%Y-%m-%d').date())
        except ValueError:
            pass
    if produit_id:
        mouvements = mouvements.filter(produit_id=produit_id)

    total_entrees = mouvements.filter(type_mouvement='ENTREE').aggregate(total=Sum('quantite'))['total'] or 0
    total_sorties = mouvements.filter(type_mouvement='SORTIE').aggregate(total=Sum('quantite'))['total'] or 0
    total_pertes = mouvements.filter(type_mouvement='PERTE').aggregate(total=Sum('quantite'))['total'] or 0

    produits = Produit.objects.all().order_by('nom')

    context = {
        'mouvements': mouvements,
        'produits': produits,
        'total_entrees': total_entrees,
        'total_sorties': total_sorties,
        'total_pertes': total_pertes,
        'type_mouvement': type_mouvement,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'produit_id': produit_id,
        'TYPE_CHOICES': MouvementStock.TYPE_CHOICES,
    }
    return render(request, 'stocks/historique_boulangerie.html', context)


# ============================================================
# 25. SAUVEGARDE DES DONNÉES
# ============================================================
from django.http import HttpResponse
from django.core import serializers


@login_required
@admin_required
def sauvegarder_donnees(request):
    data = {
        'date': timezone.now().isoformat(),
        'produits': serializers.serialize('json', Produit.objects.all()),
        'articles': serializers.serialize('json', ArticleVente.objects.all()),
        'compositions': serializers.serialize('json', CompositionArticle.objects.all()),
        'mouvements': serializers.serialize('json', MouvementStock.objects.all()),
        'fournisseurs': serializers.serialize('json', Fournisseur.objects.all()),
        'commandes': serializers.serialize('json', Commande.objects.all()),
        'lignes_commande': serializers.serialize('json', LigneCommande.objects.all()),
    }
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    filename = f"sauvegarde_epicerie_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ============================================================
# 26. RESTAURATION DES DONNÉES
# ============================================================
@login_required
@admin_required
def restaurer_donnees(request):
    if request.method == 'POST' and request.FILES.get('fichier'):
        try:
            fichier = request.FILES['fichier']
            data = json.loads(fichier.read().decode('utf-8'))

            MouvementStock.objects.all().delete()
            LigneCommande.objects.all().delete()
            Commande.objects.all().delete()
            CompositionArticle.objects.all().delete()
            ArticleVente.objects.all().delete()
            Produit.objects.all().delete()
            Fournisseur.objects.all().delete()

            for key, serialized_data in data.items():
                if key != 'date' and serialized_data:
                    for obj in serializers.deserialize('json', serialized_data):
                        obj.save()
            messages.success(request, "✅ Données restaurées avec succès !")
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de la restauration : {e}")
        return redirect('accueil')

    return render(request, 'stocks/gestion_donnees.html')


# ============================================================
# 27. RÉINITIALISATION DES DONNÉES
# ============================================================
@login_required
@admin_required
def reinitialiser_donnees(request):
    if request.method == 'POST':
        if request.POST.get('confirmation') == 'OUI':
            MouvementStock.objects.all().delete()
            LigneCommande.objects.all().delete()
            Commande.objects.all().delete()
            CompositionArticle.objects.all().delete()
            ArticleVente.objects.all().delete()
            Produit.objects.all().delete()
            Fournisseur.objects.all().delete()
            messages.success(request, "✅ Toutes les données ont été réinitialisées avec succès !")
        else:
            messages.error(request, "❌ Veuillez saisir 'OUI' pour confirmer la réinitialisation.")
        return redirect('accueil')

    return render(request, 'stocks/reinitialiser_donnees.html')


# ============================================================
# 28. AJOUTER UN MOUVEMENT MANUELLEMENT
# ============================================================
@login_required
@manager_required
def ajouter_mouvement(request):
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Mouvement ajouté avec succès !")
            return redirect('historique_boulangerie')
    else:
        form = MouvementStockForm()

    return render(request, 'stocks/mouvement_form.html', {
        'form': form,
        'titre': '➕ Ajouter un mouvement',
        'bouton': 'Ajouter',
        'icone': 'plus-circle'
    })


# ============================================================
# 29. MODIFIER UN MOUVEMENT
# ============================================================
@login_required
@manager_required
def modifier_mouvement(request, id):
    mouvement = get_object_or_404(MouvementStock, id=id)

    if request.method == 'POST':
        form = MouvementStockForm(request.POST, instance=mouvement)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Mouvement modifié avec succès !")
            return redirect('historique_boulangerie')
    else:
        form = MouvementStockForm(instance=mouvement)

    return render(request, 'stocks/mouvement_form.html', {
        'form': form,
        'titre': '✏️ Modifier un mouvement',
        'bouton': 'Enregistrer',
        'icone': 'pencil-square'
    })


# ============================================================
# 30. SUPPRIMER UN MOUVEMENT
# ============================================================
@login_required
@admin_required
def supprimer_mouvement(request, id):
    mouvement = get_object_or_404(MouvementStock, id=id)

    if request.method == 'POST':
        if mouvement.type_mouvement == 'ENTREE':
            mouvement.produit.quantite_stock -= mouvement.quantite
        elif mouvement.type_mouvement == 'SORTIE':
            mouvement.produit.quantite_stock += mouvement.quantite
        mouvement.produit.save()

        mouvement.delete()
        messages.success(request, "🗑️ Mouvement supprimé avec succès !")
        return redirect('historique_boulangerie')

    return render(request, 'stocks/mouvement_confirm_delete.html', {
        'mouvement': mouvement
    })


# ============================================================
# 31. AJOUTER UNE DIFFÉRENCE (PERTE / AJUSTEMENT)
# ============================================================
@login_required
def ajouter_difference(request):
    if request.method == 'POST':
        produit_id = request.POST.get('produit')
        quantite_str = request.POST.get('quantite')
        commentaire = request.POST.get('commentaire', 'Ajustement de stock')

        if not produit_id or not quantite_str:
            messages.error(request, "Veuillez sélectionner un produit et une quantité.")
            return redirect('accueil')

        try:
            quantite = Decimal(quantite_str)
            if quantite <= 0:
                messages.error(request, "La quantité doit être positive.")
                return redirect('accueil')

            produit = get_object_or_404(Produit, id=produit_id)

            # Réduire le stock
            produit.quantite_stock -= quantite
            produit.save()

            # Créer un mouvement de type PERTE
            MouvementStock.objects.create(
                produit=produit,
                type_mouvement='PERTE',
                quantite=quantite,
                commentaire=f"Différence saisie : {commentaire}"
            )

            messages.success(
                request,
                f"✅ Différence enregistrée : {quantite} {produit.unite} de {produit.nom} retiré(s). Motif : {commentaire}"
            )

        except (ValueError, TypeError):
            messages.error(request, "Veuillez entrer un nombre valide.")

        return redirect('accueil')

    return redirect('accueil')