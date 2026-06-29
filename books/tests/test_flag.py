from django.test import Client, TestCase

from books.models import Book, Narrator, Recording, RecordingStatus


class FlagRecordingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Flag User", email="flag@test.com", passphrase="flag-phrase"
        )
        self.book = Book.objects.create(title="Flag Book", slug="flag-book", author="Author")
        self.recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()

    def test_flag_with_reason_succeeds(self):
        resp = self.client.post(
            f"/portal/recording/{self.recording.id}/flag/",
            {"reason": "Audio quality issue"},
        )
        assert resp.status_code == 302
        self.recording.refresh_from_db()
        assert self.recording.flagged_for_review is True
        assert self.recording.flag_reason == "Audio quality issue"

    def test_flag_without_reason_shows_error(self):
        resp = self.client.post(
            f"/portal/recording/{self.recording.id}/flag/",
            {"reason": ""},
        )
        assert resp.status_code == 200
        assert b"Please provide a reason" in resp.content
        self.recording.refresh_from_db()
        assert self.recording.flagged_for_review is False

    def test_flag_requires_ownership(self):
        other = Narrator.objects.create(name="Other", email="o@t.com", passphrase="other-p")
        session = self.client.session
        session["narrator_id"] = str(other.id)
        session.save()
        resp = self.client.post(
            f"/portal/recording/{self.recording.id}/flag/",
            {"reason": "Stolen recording"},
        )
        assert resp.status_code == 404


class RecordingDetailTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Detail User", email="detail@test.com", passphrase="detail-phrase"
        )
        self.book = Book.objects.create(title="Detail Book", slug="detail-book", author="Author")
        self.recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.PENDING
        )
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()

    def test_owner_can_view_detail(self):
        resp = self.client.get(f"/portal/recording/{self.recording.id}/")
        assert resp.status_code == 200

    def test_non_owner_cannot_view_detail(self):
        other = Narrator.objects.create(name="Other", email="o@t.com", passphrase="other-p2")
        session = self.client.session
        session["narrator_id"] = str(other.id)
        session.save()
        resp = self.client.get(f"/portal/recording/{self.recording.id}/")
        assert resp.status_code == 404
