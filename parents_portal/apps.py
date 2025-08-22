from django.apps import AppConfig


class ParentsPortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parents_portal'
    verbose_name = 'Portail Parents'
    
    def ready(self):
        """Configuration au démarrage de l'application"""
        try:
            import parents_portal.signals
        except ImportError:
            pass
