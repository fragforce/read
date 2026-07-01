import os
import shutil

from django.conf import settings
from django.test import TestCase

from books.models import Book, Narrator, Recording, RecordingStatus


class DeleteRecordingSignalTest(TestCase):
    def setUp(self):
        self.narrator = Narrator.objects.create(
            name="Signal User", email="signal@test.com", passphrase="signal-test-phrase"
        )
        self.book = Book.objects.create(title="Signal Book", slug="signal-book", author="Author")
        for d in ("recordings", "processing", "finalized"):
            os.makedirs(os.path.join(settings.MEDIA_ROOT, d), exist_ok=True)

    def tearDown(self):
        for d in ("recordings", "processing", "finalized"):
            path = os.path.join(settings.MEDIA_ROOT, d)
            if os.path.exists(path):
                shutil.rmtree(path)

    def _create_recording_with_files(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        raw_path = os.path.join(settings.MEDIA_ROOT, "recordings", f"{recording.id}.webm")
        finalized_path = recording.finalized_path
        processing_path = recording.processing_path

        for path in (raw_path, finalized_path, processing_path):
            with open(path, "wb") as f:
                f.write(b"test content")

        recording.audio_file.name = f"recordings/{recording.id}.webm"
        recording.save(update_fields=["audio_file"])
        return recording

    def test_delete_removes_audio_file(self):
        recording = self._create_recording_with_files()
        raw_path = recording.audio_file.path
        assert os.path.exists(raw_path)

        recording.delete()
        assert not os.path.exists(raw_path)

    def test_delete_removes_finalized_file(self):
        recording = self._create_recording_with_files()
        assert os.path.exists(recording.finalized_path)

        finalized = recording.finalized_path
        recording.delete()
        assert not os.path.exists(finalized)

    def test_delete_removes_processing_file(self):
        recording = self._create_recording_with_files()
        assert os.path.exists(recording.processing_path)

        processing = recording.processing_path
        recording.delete()
        assert not os.path.exists(processing)

    def test_delete_without_files_does_not_error(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.PENDING
        )
        recording.delete()
