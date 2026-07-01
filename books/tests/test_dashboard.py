from django.test import Client, TestCase

from books.models import Book, Narrator, Recording, RecordingStatus


class DashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Dashboard User", email="dash@test.com", passphrase="dash-phrase"
        )
        self.book = Book.objects.create(
            title="Unique Testbook XYZ", slug="avail-book", author="Author"
        )
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()

    def test_dashboard_requires_login(self):
        client = Client()
        resp = client.get("/portal/")
        assert resp.status_code == 302

    def test_dashboard_shows_available_books(self):
        resp = self.client.get("/portal/")
        assert resp.status_code == 200
        assert b"Unique Testbook XYZ" in resp.content

    def test_dashboard_excludes_books_already_recorded(self):
        Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        resp = self.client.get("/portal/")
        assert resp.status_code == 200
        assert b"No books available for recording right now" in resp.content

    def test_dashboard_excludes_full_books(self):
        self.book.max_narrators = 1
        self.book.save()
        other = Narrator.objects.create(name="Other", email="other@test.com", passphrase="other-p")
        Recording.objects.create(book=self.book, narrator=other, status=RecordingStatus.READY)
        resp = self.client.get("/portal/")
        assert resp.status_code == 200
        assert b"No books available for recording right now" in resp.content

    def test_flagged_recording_shows_book_available(self):
        Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY,
            flagged_for_review=True, flag_reason="Bad audio",
        )
        resp = self.client.get("/portal/")
        assert b"Unique Testbook XYZ" in resp.content

    def test_flagged_recording_not_counted_toward_max_narrators(self):
        self.book.max_narrators = 1
        self.book.save()
        other = Narrator.objects.create(name="Other", email="other@test.com", passphrase="other-p2")
        Recording.objects.create(
            book=self.book, narrator=other, status=RecordingStatus.READY,
            flagged_for_review=True, flag_reason="Noise",
        )
        resp = self.client.get("/portal/")
        assert b"Unique Testbook XYZ" in resp.content

    def test_flagged_recording_detail_shows_rerecord_link(self):
        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY,
            flagged_for_review=True, flag_reason="Background noise",
        )
        resp = self.client.get(f"/portal/recording/{recording.id}/")
        assert b"Re-record this book" in resp.content
        assert f"/portal/preflight/{self.book.id}/".encode() in resp.content

    def test_invalid_narrator_in_session_redirects(self):
        client = Client()
        session = client.session
        session["narrator_id"] = "00000000-0000-0000-0000-000000000000"
        session.save()
        resp = client.get("/portal/")
        assert resp.status_code == 302
