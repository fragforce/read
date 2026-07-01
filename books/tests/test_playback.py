from datetime import date, timedelta

from django.test import Client, TestCase

from books.models import Book, Narrator, QRCode, Recording, RecordingStatus


class LicenseExpiryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Test Narrator", email="test@example.com", passphrase="test-phrase"
        )
        self.book = Book.objects.create(title="Test Book", slug="test-book", author="Author")
        self.recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )

    def test_playback_allowed_when_no_expiry(self):
        resp = self.client.get(f"/b/play/{self.book.id}/")
        assert resp.status_code == 200
        assert b"No Longer Available" not in resp.content

    def test_playback_allowed_when_expiry_in_future(self):
        self.book.license_expiry = date.today() + timedelta(days=30)
        self.book.save()
        resp = self.client.get(f"/b/play/{self.book.id}/")
        assert resp.status_code == 200
        assert b"No Longer Available" not in resp.content

    def test_playback_blocked_when_expired(self):
        self.book.license_expiry = date.today() - timedelta(days=1)
        self.book.save()
        resp = self.client.get(f"/b/play/{self.book.id}/")
        assert resp.status_code == 200
        assert b"No Longer Available" in resp.content

    def test_audio_serving_blocked_when_expired(self):
        self.book.license_expiry = date.today() - timedelta(days=1)
        self.book.save()
        resp = self.client.get(f"/b/audio/{self.recording.id}/")
        assert resp.status_code == 404


class PasswordRateLimitTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Test Narrator", email="test@example.com", passphrase="test-phrase"
        )
        self.book = Book.objects.create(title="PW Book", slug="pw-book", author="Author")
        self.recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        self.qr = QRCode.objects.create(
            book=self.book, recording=self.recording, label_text="test", password="correct-pass"
        )

    def test_wrong_password_shows_error(self):
        resp = self.client.post(f"/b/play/{self.book.id}/", {"password": "wrong"})
        assert resp.status_code == 200
        assert b"Incorrect password" in resp.content

    def test_lockout_after_5_attempts(self):
        for _ in range(5):
            self.client.post(f"/b/play/{self.book.id}/", {"password": "wrong"})
        resp = self.client.post(f"/b/play/{self.book.id}/", {"password": "wrong"})
        assert b"Too many attempts" in resp.content

    def test_correct_password_clears_attempts(self):
        for _ in range(3):
            self.client.post(f"/b/play/{self.book.id}/", {"password": "wrong"})
        resp = self.client.post(f"/b/play/{self.book.id}/", {"password": "correct-pass"})
        assert b"audio-player" in resp.content

    def test_correct_password_after_lockout_still_blocked(self):
        for _ in range(5):
            self.client.post(f"/b/play/{self.book.id}/", {"password": "wrong"})
        resp = self.client.post(f"/b/play/{self.book.id}/", {"password": "correct-pass"})
        assert b"Too many attempts" in resp.content


class PlaybackViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Play User", email="play@test.com", passphrase="play-phrase"
        )
        self.book = Book.objects.create(title="Play Book", slug="play-book", author="Author")

    def test_playback_404_when_no_recordings(self):
        resp = self.client.get(f"/b/play/{self.book.id}/")
        assert resp.status_code == 404

    def test_playback_specific_recording(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        resp = self.client.get(f"/b/play/{self.book.id}/{recording.id}/")
        assert resp.status_code == 200

    def test_playback_specific_wrong_book_404(self):
        other_book = Book.objects.create(title="Other", slug="other-book", author="Author")
        recording = Recording.objects.create(
            book=other_book, narrator=self.narrator, status=RecordingStatus.READY
        )
        resp = self.client.get(f"/b/play/{self.book.id}/{recording.id}/")
        assert resp.status_code == 404

    def test_playback_no_password_shows_player(self):
        Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        resp = self.client.get(f"/b/play/{self.book.id}/")
        assert resp.status_code == 200
        assert b"audio-player" in resp.content

    def test_narrator_shown_before_password_entry(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        QRCode.objects.create(
            book=self.book, recording=recording, label_text="test", password="secret"
        )
        resp = self.client.get(f"/b/play/{self.book.id}/")
        assert resp.status_code == 200
        assert b"Read by: Play User" in resp.content
        assert b"audio-player" not in resp.content

    def test_session_unlock_persists(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        QRCode.objects.create(
            book=self.book, recording=recording, label_text="test", password="secret"
        )
        self.client.post(f"/b/play/{self.book.id}/", {"password": "secret"})
        resp = self.client.get(f"/b/play/{self.book.id}/")
        assert b"audio-player" in resp.content
