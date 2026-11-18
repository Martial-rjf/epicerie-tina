from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ======================================================
    # 0. VITRINE PUBLIQUE (page d'accueil avant connexion)
    # ======================================================
    path('', views.vitrine, name='vitrine'),

    # ======================================================
    # AUTHENTIFICATION (vues intégrées Django)
    # ======================================================
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='registration/change_password.html',
        success_url='/accueil/'
    ), name='change_password'),

    # ======================================================
    # 1. TABLEAU DE BORD
    # ======================================================
    path('accueil/', views.accueil, name='accueil'),
    path('detail-ventes-jour/', views.detail_ventes_jour, name='detail_ventes_jour'),

    # ======================================================
    # 2. GESTION DES PRODUITS
    # ======================================================
    path('produits/', views.gestion_produits, name='gestion_produits'),
    path('produits/ajouter/', views.ajouter_produit, name='ajouter_produit'),
    path('produits/<int:id>/modifier/', views.modifier_produit, name='modifier_produit'),
    path('produits/<int:id>/supprimer/', views.supprimer_produit, name='supprimer_produit'),

    # ======================================================
    # 3. ARTICLES DE VENTE
    # ======================================================
    path('articles/', views.liste_articles, name='liste_articles'),
    path('articles/ajouter/', views.ajouter_article, name='ajouter_article'),
    path('articles/<int:id>/modifier/', views.modifier_article, name='modifier_article'),
    path('articles/<int:id>/supprimer/', views.supprimer_article, name='supprimer_article'),
    path('articles/<int:id>/vendre/', views.vente_article, name='vente_article'),

    # ======================================================
    # 4. COMPOSITIONS
    # ======================================================
    path('articles/<int:article_id>/composition/ajouter/', views.ajouter_composition, name='ajouter_composition'),
    path('compositions/<int:id>/modifier/', views.modifier_composition, name='modifier_composition'),
    path('compositions/<int:id>/supprimer/', views.supprimer_composition, name='supprimer_composition'),

    # ======================================================
    # 5. FICHE DE STOCK
    # ======================================================
    path('fiche-stock/', views.fiche_stock, name='fiche_stock'),
    path('fiche-stock/export-pdf/', views.export_pdf_fiche_stock, name='export_pdf_fiche_stock'),

    # ======================================================
    # 6. HISTORIQUE
    # ======================================================
    path('historique/', views.historique_boulangerie, name='historique_boulangerie'),
    path('historique/mouvements/', views.historique_mouvements, name='historique_mouvements'),

    # ======================================================
    # 7. PERTES
    # ======================================================
    path('pertes/', views.gestion_pertes, name='gestion_pertes'),
    path('pertes/<int:id>/supprimer/', views.supprimer_perte, name='supprimer_perte'),
    path('ajouter-difference/', views.ajouter_difference, name='ajouter_difference'),

    # ======================================================
    # 8. FOURNISSEURS
    # ======================================================
    path('fournisseurs/', views.gestion_fournisseurs, name='gestion_fournisseurs'),

    # ======================================================
    # 9. COMMANDES
    # ======================================================
    path('commandes/', views.liste_commandes, name='liste_commandes'),
    path('commandes/creer/', views.creer_commande, name='creer_commande'),
    path('commandes/<int:id>/', views.detail_commande, name='detail_commande'),
    path('commandes/<int:id>/supprimer/', views.supprimer_commande, name='supprimer_commande'),

    # ======================================================
    # 10. MOUVEMENTS MANUELS
    # ======================================================
    path('mouvements/ajouter/', views.ajouter_mouvement, name='ajouter_mouvement'),
    path('mouvements/<int:id>/modifier/', views.modifier_mouvement, name='modifier_mouvement'),
    path('mouvements/<int:id>/supprimer/', views.supprimer_mouvement, name='supprimer_mouvement'),

    # ======================================================
    # 11. GESTION DES DONNÉES
    # ======================================================
    path('donnees/sauvegarder/', views.sauvegarder_donnees, name='sauvegarder_donnees'),
    path('donnees/restaurer/', views.restaurer_donnees, name='restaurer_donnees'),
    path('donnees/reinitialiser/', views.reinitialiser_donnees, name='reinitialiser_donnees'),

# ======================================================
# RÉINITIALISATION DE MOT DE PASSE
# ======================================================
path('password-reset/',
     auth_views.PasswordResetView.as_view(
         template_name='registration/password_reset_form.html',
         email_template_name='registration/password_reset_email.html',
         subject_template_name='registration/password_reset_subject.txt',
         success_url='/password-reset/done/'
     ),
     name='password_reset'),

path('password-reset/done/',
     auth_views.PasswordResetDoneView.as_view(
         template_name='registration/password_reset_done.html'
     ),
     name='password_reset_done'),

path('reset/<uidb64>/<token>/',
     auth_views.PasswordResetConfirmView.as_view(
         template_name='registration/password_reset_confirm.html',
         success_url='/login/'
     ),
     name='password_reset_confirm'),

path('reset/done/',
     auth_views.PasswordResetCompleteView.as_view(
         template_name='registration/password_reset_complete.html'
     ),
     name='password_reset_complete'),
]