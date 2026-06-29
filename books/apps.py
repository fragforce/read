import os
import sys
import threading

from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "books"

    def ready(self):

        if any(cmd in sys.argv for cmd in ["migrate", "collectstatic", "makemigrations", "createsuperuser", "check"]):
            return

        if os.environ.get("RUN_MAIN") == "true" or "runserver" not in sys.argv:
            from .processing import recover_pending_recordings
            threading.Thread(
                target=recover_pending_recordings,
                daemon=True,
                name="remux-recovery",
            ).start()
