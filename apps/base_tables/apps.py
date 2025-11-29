from django.apps import AppConfig


class BaseTablesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.base_tables'
