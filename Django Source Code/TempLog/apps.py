from django.apps import AppConfig
from django.conf import settings

class TemplogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'TempLog'

    def ready(self):
        # define default email settings
        from .models import EmailSetting
        email_setting, created = EmailSetting.objects.get_or_create(id=1)
        settings.EMAIL_HOST = email_setting.EMAIL_HOST
        settings.EMAIL_USE_TLS = email_setting.EMAIL_USE_TLS
        settings.EMAIL_PORT = email_setting.EMAIL_PORT
        settings.EMAIL_HOST_USER = email_setting.EMAIL_HOST_USER
        if email_setting.EMAIL_HOST_PASSWORD is not None:
            settings.EMAIL_HOST_PASSWORD = email_setting.EMAIL_HOST_PASSWORD
        # define a fake sensor device for email notification purpose
        from .models import Device
        fake_sensor, created = Device.objects.get_or_create(Name='All',Is_Active=False)