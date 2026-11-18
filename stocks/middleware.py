from django.shortcuts import redirect

class RedirectToLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si l'utilisateur est connecté et qu'il est sur la page d'accueil '/'
        if request.user.is_authenticated and request.path == '/':
            return redirect('/login/')
        response = self.get_response(request)
        return response