class SecurityHeadersMiddleware:
    """En-têtes défensifs pour l'API, y compris ses réponses d'erreur."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.setdefault("X-XSS-Protection", "0")
        if request.path.startswith(("/api/auth/", "/api/profile/", "/api/contacts/")):
            response["Cache-Control"] = "no-store"
        return response
