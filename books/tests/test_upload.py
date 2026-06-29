from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from books.models import Attestation, Book, Narrator, Recording


class DurationValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Test Narrator", email="test@example.com", passphrase="test-phrase"
        )
        self.book = Book.objects.create(title="Dur Book", slug="dur-book", author="Author")
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session[f"preflight_{self.book.id}"] = True
        session.save()

    def test_negative_duration_rejected(self):
        audio = SimpleUploadedFile("test.webm", b"fake audio", content_type="audio/webm")
        resp = self.client.post(
            f"/portal/upload/{self.book.id}/",
            {"audio": audio, "duration": "-10", "attestation_text": "I attest"},
        )
        assert resp.status_code == 400
        assert b"out of bounds" in resp.content

    def test_excessive_duration_rejected(self):
        audio = SimpleUploadedFile("test.webm", b"fake audio", content_type="audio/webm")
        resp = self.client.post(
            f"/portal/upload/{self.book.id}/",
            {"audio": audio, "duration": "7200", "attestation_text": "I attest"},
        )
        assert resp.status_code == 400
        assert b"out of bounds" in resp.content

    def test_valid_duration_accepted(self):
        audio = SimpleUploadedFile("test.webm", b"fake audio", content_type="audio/webm")
        resp = self.client.post(
            f"/portal/upload/{self.book.id}/",
            {"audio": audio, "duration": "120", "attestation_text": "I attest"},
        )
        assert resp.status_code == 200


class AttestationValidationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Test Narrator", email="test@example.com", passphrase="test-phrase"
        )
        self.book = Book.objects.create(title="Att Book", slug="att-book", author="Author")
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session[f"preflight_{self.book.id}"] = True
        session.save()

    def test_attestation_too_long_rejected(self):
        audio = SimpleUploadedFile("test.webm", b"fake audio", content_type="audio/webm")
        resp = self.client.post(
            f"/portal/upload/{self.book.id}/",
            {"audio": audio, "duration": "60", "attestation_text": "x" * 2001},
        )
        assert resp.status_code == 400
        assert b"too long" in resp.content

    def test_missing_attestation_rejected(self):
        audio = SimpleUploadedFile("test.webm", b"fake audio", content_type="audio/webm")
        resp = self.client.post(
            f"/portal/upload/{self.book.id}/",
            {"audio": audio, "duration": "60", "attestation_text": ""},
        )
        assert resp.status_code == 400
        assert b"Attestation is required" in resp.content


class UploadSizeLimitTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Test Narrator", email="test@example.com", passphrase="test-phrase"
        )
        self.book = Book.objects.create(title="Size Book", slug="size-book", author="Author")
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session[f"preflight_{self.book.id}"] = True
        session.save()

    def test_oversized_file_rejected(self):
        with override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=100):
            audio = SimpleUploadedFile("test.webm", b"x" * 200, content_type="audio/webm")
            resp = self.client.post(
                f"/portal/upload/{self.book.id}/",
                {"audio": audio, "duration": "60", "attestation_text": "I attest"},
            )
            assert resp.status_code == 400
            assert b"too large" in resp.content


class UploadRecordingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Upload User", email="upload@test.com", passphrase="upload-phrase"
        )
        self.book = Book.objects.create(title="Upload Book", slug="upload-book", author="Author")
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session[f"preflight_{self.book.id}"] = True
        session.save()

    def test_missing_audio_file_rejected(self):
        resp = self.client.post(
            f"/portal/upload/{self.book.id}/",
            {"duration": "60", "attestation_text": "I attest"},
        )
        assert resp.status_code == 400
        assert b"No audio file" in resp.content

    def test_unsupported_content_type_rejected(self):
        audio = SimpleUploadedFile("test.mp3", b"fake", content_type="audio/mpeg")
        resp = self.client.post(
            f"/portal/upload/{self.book.id}/",
            {"audio": audio, "duration": "60", "attestation_text": "I attest"},
        )
        assert resp.status_code == 400
        assert b"Unsupported audio format" in resp.content

    def test_successful_upload_creates_recording_and_attestation(self):
        audio = SimpleUploadedFile("test.webm", b"fake audio", content_type="audio/webm")
        resp = self.client.post(
            f"/portal/upload/{self.book.id}/",
            {"audio": audio, "duration": "120", "attestation_text": "I hereby attest"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "redirect" in data
        recording = Recording.objects.get(id=data["id"])
        assert recording.book == self.book
        assert recording.narrator == self.narrator
        assert recording.duration_seconds == 120
        assert Attestation.objects.filter(recording=recording).exists()

    def test_upload_requires_login(self):
        client = Client()
        audio = SimpleUploadedFile("test.webm", b"fake audio", content_type="audio/webm")
        resp = client.post(
            f"/portal/upload/{self.book.id}/",
            {"audio": audio, "duration": "60", "attestation_text": "I attest"},
        )
        assert resp.status_code == 302
