from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cases'
    
    def ready(self):
        """Importa signals quando o app está pronto"""
        import apps.cases.signals  # noqa
    verbose_name = 'Processos'
