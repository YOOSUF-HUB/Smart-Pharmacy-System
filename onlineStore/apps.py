from django.apps import AppConfig


class OnlinestoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'onlineStore'

    def ready(self):
        import onlineStore.signals
        