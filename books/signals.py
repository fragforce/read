import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Recording


@receiver(post_delete, sender=Recording)
def delete_recording_file(sender, instance, **kwargs):
    if instance.audio_file:
        instance.audio_file.delete(save=False)

    finalized = instance.finalized_path
    if os.path.exists(finalized):
        try:
            os.remove(finalized)
        except OSError:
            pass

    processing = instance.processing_path
    if os.path.exists(processing):
        try:
            os.remove(processing)
        except OSError:
            pass
