import os
import shutil

from django.conf import settings
from django.test import Client, TestCase

from books.models import Book, Narrator, Recording, RecordingStatus


class ServeRecordingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Serve User", email="serve@test.com", passphrase="serve-phrase"
        )
        self.book = Book.objects.create(title="Serve Book", slug="serve-book", author="Author")
        self.recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        self.finalized_dir = os.path.join(settings.MEDIA_ROOT, "finalized")
        os.makedirs(self.finalized_dir, exist_ok=True)
        self.finalized_path = os.path.join(self.finalized_dir, f"{self.recording.id}.webm")
        with open(self.finalized_path, "wb") as f:
            f.write(b"A" * 1000)

    def tearDown(self):
        if os.path.exists(self.finalized_dir):
            shutil.rmtree(self.finalized_dir)

    def test_full_file_served(self):
        resp = self.client.get(f"/b/audio/{self.recording.id}/")
        assert resp.status_code == 200
        assert resp["Content-Length"] == "1000"

    def test_range_request(self):
        resp = self.client.get(
            f"/b/audio/{self.recording.id}/",
            HTTP_RANGE="bytes=0-99",
        )
        assert resp.status_code == 206
        assert resp["Content-Length"] == "100"
        assert "bytes 0-99/1000" in resp["Content-Range"]

    def test_range_request_open_ended(self):
        resp = self.client.get(
            f"/b/audio/{self.recording.id}/",
            HTTP_RANGE="bytes=900-",
        )
        assert resp.status_code == 206
        assert resp["Content-Length"] == "100"

    def test_pending_recording_inaccessible_to_non_owner(self):
        self.recording.status = RecordingStatus.PENDING
        self.recording.save()
        resp = self.client.get(f"/b/audio/{self.recording.id}/")
        assert resp.status_code == 404

    def test_pending_recording_accessible_to_owner(self):
        self.recording.status = RecordingStatus.PENDING
        self.recording.save()
        recordings_dir = os.path.join(settings.MEDIA_ROOT, "recordings")
        os.makedirs(recordings_dir, exist_ok=True)
        raw_path = os.path.join(recordings_dir, f"{self.recording.id}.webm")
        with open(raw_path, "wb") as f:
            f.write(b"B" * 500)
        self.recording.audio_file.name = f"recordings/{self.recording.id}.webm"
        self.recording.save(update_fields=["audio_file"])

        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()
        resp = self.client.get(f"/b/audio/{self.recording.id}/")
        assert resp.status_code == 200
        assert resp["Content-Length"] == "500"

    def test_missing_file_returns_404(self):
        os.unlink(self.finalized_path)
        resp = self.client.get(f"/b/audio/{self.recording.id}/")
        assert resp.status_code == 404
