from django.apps import AppConfig


class TourConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tour'

    def ready(self):
        # Template tags'i yükle
        from django.template.defaultfilters import register
        from .templatetags import custom_filters
