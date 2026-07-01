import os
import sys
import threading

from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "books"

    def ready(self):
        import books.signals  # noqa: F401

        if not self._should_recover():
            return

        from .processing import recover_pending_recordings
        threading.Thread(
            target=recover_pending_recordings,
            daemon=True,
            name="remux-recovery",
        ).start()

    def _should_recover(self):
        if "gunicorn" in sys.argv[0]:
            return True
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") == "true":
            return True
        return False
