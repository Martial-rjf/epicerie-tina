import os
import sys
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # Ajouter le chemin du projet pour que Django trouve tout
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    
    # Lancer le serveur
    execute_from_command_line(['', 'runserver', '127.0.0.1:8000'])