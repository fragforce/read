import os
import shutil
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from books.models import Book, Narrator, QRCode, Recording, RecordingStatus
from books.processing import recover_pending_recordings, remux_recording, spawn_remux


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

    def test_no_audio_file_sets_failed(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.PENDING
        )
        remux_recording(recording.id)
        recording.refresh_from_db()
        assert recording.status == RecordingStatus.FAILED

    def test_missing_raw_file_sets_failed(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.PENDING
        )
        recording.audio_file.name = "recordings/nonexistent.webm"
        recording.save(update_fields=["audio_file"])
        remux_recording(recording.id)
        recording.refresh_from_db()
        assert recording.status == RecordingStatus.FAILED

    @patch("subprocess.run")
    def test_qr_creation_failure_does_not_break_remux(self, mock_run):
        recording = self._create_recording_with_file()
        finalized_path = os.path.join(settings.MEDIA_ROOT, "finalized", f"{recording.id}.webm")
        os.makedirs(os.path.dirname(finalized_path), exist_ok=True)

        def fake_ffmpeg(*args, **kwargs):
            with open(finalized_path, "wb") as f:
                f.write(b"remuxed")
            return type("Result", (), {"returncode": 0, "stderr": ""})()

        mock_run.side_effect = fake_ffmpeg

        with patch("books.processing._create_qr_for_recording", side_effect=Exception("QR error")):
            remux_recording(recording.id)

        recording.refresh_from_db()
        assert recording.status == RecordingStatus.READY

    def test_spawn_remux_returns_thread(self):
        recording = self._create_recording_with_file()
        thread = spawn_remux(recording.id)
        thread.join(timeout=5)
        assert not thread.is_alive()

    def test_recover_pending_spawns_remux(self):
        recording = self._create_recording_with_file()
        with patch("books.processing.spawn_remux") as mock_spawn:
            recover_pending_recordings()
        mock_spawn.assert_called_once_with(recording.id)
