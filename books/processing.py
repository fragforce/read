import logging
import os
import shutil
import subprocess
import threading

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


def ensure_directories():
    for subdir in ("processing", "finalized"):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, subdir), exist_ok=True)


def remux_recording(recording_id):
    from .models import Recording, RecordingStatus

    ensure_directories()

    processing_path = os.path.join(settings.MEDIA_ROOT, "processing", f"{recording_id}.webm")
    finalized_path = os.path.join(settings.MEDIA_ROOT, "finalized", f"{recording_id}.webm")

    with transaction.atomic():
        locked = (
            Recording.objects.select_for_update(skip_locked=True)
            .filter(id=recording_id, status__in=[RecordingStatus.PENDING, RecordingStatus.PROCESSING])
            .first()
        )
        if not locked:
            return
        locked.status = RecordingStatus.PROCESSING
        locked.save(update_fields=["status"])

    try:
        recording = Recording.objects.get(id=recording_id)
        if not recording.audio_file:
            raise FileNotFoundError(f"Recording {recording_id} has no audio file")
        raw_path = recording.audio_file.path
        if not os.path.exists(raw_path):
            raise FileNotFoundError(f"Raw recording file not found: {raw_path}")

        shutil.copy2(raw_path, processing_path)

        result = subprocess.run(
            ["ffmpeg", "-y", "-i", processing_path, "-codec", "copy", finalized_path],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed (code {result.returncode}): {result.stderr}")

    except Exception:
        logger.exception("Failed to remux recording %s", recording_id)
        if os.path.exists(finalized_path):
            try:
                os.remove(finalized_path)
            except OSError:
                pass
        Recording.objects.filter(id=recording_id).update(status=RecordingStatus.FAILED)
        if os.path.exists(processing_path):
            try:
                os.remove(processing_path)
            except OSError:
                pass
        return

    if os.path.exists(processing_path):
        try:
            os.remove(processing_path)
        except OSError:
            pass
    Recording.objects.filter(id=recording_id).update(status=RecordingStatus.READY)
    logger.info("Recording %s remuxed successfully", recording_id)


def spawn_remux(recording_id):
    thread = threading.Thread(
        target=remux_recording,
        args=(recording_id,),
        daemon=True,
        name=f"remux-{recording_id}",
    )
    thread.start()
    return thread


def recover_pending_recordings():
    from .models import Recording, RecordingStatus

    ensure_directories()

    stuck = Recording.objects.filter(
        status__in=[RecordingStatus.PENDING, RecordingStatus.PROCESSING]
    )
    count = stuck.count()
    if count:
        logger.info("Recovering %d stuck recordings for remuxing", count)

    for recording in stuck:
        spawn_remux(recording.id)
