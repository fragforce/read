from datetime import timedelta

from django.test import Client, TestCase
from django.utils import timezone

from books.models import Narrator
from registration.models import InviteLink


class InviteRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.invite = InviteLink.objects.create(token="test-invite-token", label="Test Invite")

    def test_valid_invite_shows_form(self):
        resp = self.client.get("/register/invite/test-invite-token/")
        assert resp.status_code == 200

    def test_invalid_invite_returns_404(self):
        resp = self.client.get("/register/invite/nonexistent/")
        assert resp.status_code == 404

    def test_used_invite_returns_404(self):
        self.invite.used = True
        self.invite.save()
        resp = self.client.get("/register/invite/test-invite-token/")
        assert resp.status_code == 404

    def test_expired_invite_returns_404(self):
        self.invite.expires_at = timezone.now() - timedelta(hours=1)
        self.invite.save()
        resp = self.client.get("/register/invite/test-invite-token/")
        assert resp.status_code == 404

    def test_successful_registration_via_invite(self):
        resp = self.client.post("/register/invite/test-invite-token/", {
            "name": "Invited Reader", "email": "invited@test.com"
        })
        assert resp.status_code == 302
        narrator = Narrator.objects.get(email="invited@test.com")
        assert narrator.name == "Invited Reader"
        self.invite.refresh_from_db()
        assert self.invite.used is True
        assert self.invite.narrator == narrator

    def test_missing_fields_shows_error(self):
        resp = self.client.post("/register/invite/test-invite-token/", {
            "name": "", "email": ""
        })
        assert resp.status_code == 200
        assert b"Name and email are required" in resp.content
