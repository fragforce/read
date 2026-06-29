from django.test import Client, TestCase

from books.models import Narrator


class ProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Profile User", email="profile@test.com", passphrase="profile-phrase"
        )
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()

    def test_profile_get_shows_form(self):
        resp = self.client.get("/portal/profile/")
        assert resp.status_code == 200
        assert b"Profile User" in resp.content

    def test_profile_update_succeeds(self):
        resp = self.client.post("/portal/profile/", {
            "name": "Updated Name", "email": "updated@test.com"
        })
        assert resp.status_code == 200
        self.narrator.refresh_from_db()
        assert self.narrator.name == "Updated Name"
        assert self.narrator.email == "updated@test.com"

    def test_profile_missing_fields_shows_error(self):
        resp = self.client.post("/portal/profile/", {"name": "", "email": ""})
        assert resp.status_code == 200
        assert b"Name and email are required" in resp.content

    def test_profile_requires_login(self):
        client = Client()
        resp = client.get("/portal/profile/")
        assert resp.status_code == 302
