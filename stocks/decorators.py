from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def admin_required(function=None, redirect_field_name=None, login_url=None):
    """
    Vérifie que l'utilisateur est un superutilisateur OU dans le groupe 'Admin'
    """
    def test(user):
        if user.is_authenticated and (user.is_superuser or user.groups.filter(name='Admin').exists()):
            return True
        raise PermissionDenied("Accès réservé aux administrateurs.")
    return user_passes_test(test, login_url=login_url, redirect_field_name=redirect_field_name)(function)


def manager_required(function=None, redirect_field_name=None, login_url=None):
    """
    Vérifie que l'utilisateur est un superutilisateur OU dans le groupe 'Admin' ou 'Manager'
    """
    def test(user):
        if user.is_authenticated and (user.is_superuser or user.groups.filter(name='Admin').exists() or user.groups.filter(name='Manager').exists()):
            return True
        raise PermissionDenied("Accès réservé aux managers et administrateurs.")
    return user_passes_test(test, login_url=login_url, redirect_field_name=redirect_field_name)(function)


def employee_required(function=None, redirect_field_name=None, login_url=None):
    """
    Vérifie que l'utilisateur est authentifié (accès à toutes les pages)
    """
    def test(user):
        if user.is_authenticated:
            return True
        raise PermissionDenied("Vous devez être connecté.")
    return user_passes_test(test, login_url=login_url, redirect_field_name=redirect_field_name)(function)