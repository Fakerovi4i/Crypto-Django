from django.apps import AppConfig


class CryptoConfig(AppConfig):
    name = "crypto"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import crypto.signals  # noqa: F401
