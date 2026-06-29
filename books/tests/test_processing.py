import os
import shutil
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from books.models import Book, Narrator, QRCode, Recording, RecordingStatus
from books.processing import remux_recording


class RemuxRecordingTest(TestCase):
    def setUp(self):
        self.narrator = Narrator.objects.create(
            name="Remux User", email="remux@test.com", passphrase="remux-phrase"
        )
        self.book = Book.objects.create(title="Remux Book", slug="remux-book", author="Author")
        self.recordings_dir = os.path.join(settings.MEDIA_ROOT, "recordings")
        os.makedirs(self.recordings_dir, exist_ok=True)

    def tearDown(self):
        for d in ("recordings", "processing", "finalized"):
            path = os.path.join(settings.MEDIA_ROOT, d)
            if os.path.exists(path):
                shutil.rmtree(path)

    def _create_recording_with_file(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.PENDING,
        )
        file_path = os.path.join(self.recordings_dir, f"{recording.id}.webm")
        with open(file_path, "wb") as f:
            f.write(b"fake audio content")
        recording.audio_file.name = f"recordings/{recording.id}.webm"
        recording.save(update_fields=["audio_file"])
        return recording

    @patch("subprocess.run")
    def test_successful_remux(self, mock_run):
        mock_run.return_value = type("Result", (), {"returncode": 0, "stderr": ""})()
        recording = self._create_recording_with_file()
        finalized_path = os.path.join(settings.MEDIA_ROOT, "finalized", f"{recording.id}.webm")
        os.makedirs(os.path.dirname(finalized_path), exist_ok=True)

        def fake_ffmpeg(*args, **kwargs):
            with open(finalized_path, "wb") as f:
                f.write(b"remuxed")
            return type("Result", (), {"returncode": 0, "stderr": ""})()

        mock_run.side_effect = fake_ffmpeg
        remux_recording(recording.id)

        recording.refresh_from_db()
        assert recording.status == RecordingStatus.READY
        assert QRCode.objects.filter(recording=recording).exists()

    @patch("subprocess.run")
    def test_failed_remux_sets_status(self, mock_run):
        mock_run.return_value = type("Result", (), {"returncode": 1, "stderr": "error"})()
        recording = self._create_recording_with_file()
        remux_recording(recording.id)

        recording.refresh_from_db()
        assert recording.status == RecordingStatus.FAILED

    def test_already_processed_skips(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        remux_recording(recording.id)
        recording.refresh_from_db()
        assert recording.status == RecordingStatus.READY

    @patch("subprocess.run")
    def test_no_duplicate_qr_code_on_reprocess(self, mock_run):
        recording = self._create_recording_with_file()
        QRCode.objects.create(book=self.book, recording=recording, label_text="Existing")
        finalized_path = os.path.join(settings.MEDIA_ROOT, "finalized", f"{recording.id}.webm")
        os.makedirs(os.path.dirname(finalized_path), exist_ok=True)

        def fake_ffmpeg(*args, **kwargs):
            with open(finalized_path, "wb") as f:
                f.write(b"remuxed")
            return type("Result", (), {"returncode": 0, "stderr": ""})()

        mock_run.side_effect = fake_ffmpeg
        remux_recording(recording.id)

        assert QRCode.objects.filter(recording=recording).count() == 1
