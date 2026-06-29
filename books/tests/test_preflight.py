from django.test import Client, TestCase

from books.models import Book, Narrator


class PreflightTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Preflight User", email="pre@test.com", passphrase="pre-phrase"
        )
        self.book = Book.objects.create(
            title="Preflight Book", slug="preflight-book", author="Author",
            public_domain=True, full_text="Once upon a time...",
        )
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()

    def test_preflight_shows_checklist(self):
        resp = self.client.get(f"/portal/preflight/{self.book.id}/")
        assert resp.status_code == 200

    def test_preflight_incomplete_shows_error(self):
        resp = self.client.post(f"/portal/preflight/{self.book.id}/", {"quiet_room": "on"})
        assert resp.status_code == 200
        assert b"Please confirm all items" in resp.content

    def test_preflight_complete_redirects_to_record(self):
        resp = self.client.post(f"/portal/preflight/{self.book.id}/", {
            "quiet_room": "on",
            "mic_connected": "on",
            "water": "on",
            "phone_silenced": "on",
        })
        assert resp.status_code == 302
        assert f"/portal/record/{self.book.id}/" in resp.url

    def test_non_public_domain_requires_physical_book_item(self):
        self.book.public_domain = False
        self.book.full_text = ""
        self.book.save()
        resp = self.client.post(f"/portal/preflight/{self.book.id}/", {
            "quiet_room": "on",
            "mic_connected": "on",
            "water": "on",
            "phone_silenced": "on",
        })
        assert resp.status_code == 200
        assert b"Please confirm all items" in resp.content

    def test_non_public_domain_complete_with_physical_book(self):
        self.book.public_domain = False
        self.book.full_text = ""
        self.book.save()
        resp = self.client.post(f"/portal/preflight/{self.book.id}/", {
            "quiet_room": "on",
            "mic_connected": "on",
            "water": "on",
            "phone_silenced": "on",
            "physical_book": "on",
        })
        assert resp.status_code == 302


class RecordViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Record User", email="rec@test.com", passphrase="rec-phrase"
        )
        self.book = Book.objects.create(title="Record Book", slug="record-book", author="Author")
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()

    def test_record_without_preflight_redirects(self):
        resp = self.client.get(f"/portal/record/{self.book.id}/")
        assert resp.status_code == 302
        assert "preflight" in resp.url

    def test_record_with_preflight_shows_page(self):
        session = self.client.session
        session[f"preflight_{self.book.id}"] = True
        session.save()
        resp = self.client.get(f"/portal/record/{self.book.id}/")
        assert resp.status_code == 200
