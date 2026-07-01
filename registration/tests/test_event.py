from datetime import timedelta

from django.test import Client, TestCase, override_settings
from django.utils import timezone

from books.models import Narrator
from registration.models import EventCode


class EventRegistrationRateLimitTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.event_code = EventCode.objects.create(code="TESTEVENT")

    def test_wrong_event_code_shows_error(self):
        resp = self.client.post("/register/event/", {
            "code": "WRONG", "name": "Test", "email": "t@t.com"
        })
        assert resp.status_code == 200
        assert b"Invalid or expired" in resp.content

    def test_lockout_after_5_attempts(self):
        for _ in range(5):
            self.client.post("/register/event/", {
                "code": "WRONG", "name": "Test", "email": "t@t.com"
            })
        resp = self.client.post("/register/event/", {
            "code": "WRONG", "name": "Test", "email": "t@t.com"
        })
        assert b"Too many attempts" in resp.content

    def test_unlock_param_clears_lockout(self):
        for _ in range(5):
            self.client.post("/register/event/", {
                "code": "WRONG", "name": "Test", "email": "t@t.com"
            })
        with override_settings(LOGIN_UNLOCK_CODE="admin-secret"):
            self.client.get("/register/event/?unlock=admin-secret")
            resp = self.client.post("/register/event/", {
                "code": "WRONG", "name": "Test", "email": "t@t.com"
            })
            assert b"Too many attempts" not in resp.content

    def test_unlock_param_ignored_when_not_configured(self):
        for _ in range(5):
            self.client.post("/register/event/", {
                "code": "WRONG", "name": "Test", "email": "t@t.com"
            })
        self.client.get("/register/event/?unlock=anything")
        resp = self.client.post("/register/event/", {
            "code": "WRONG", "name": "Test", "email": "t@t.com"
        })
        assert b"Too many attempts" in resp.content


class EventRegistrationSuccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.event_code = EventCode.objects.create(code="VALIDEVENT")

    def test_valid_registration_creates_narrator(self):
        resp = self.client.post("/register/event/", {
            "code": "VALIDEVENT", "name": "New Reader", "email": "reader@test.com"
        })
        assert resp.status_code == 302
        narrator = Narrator.objects.get(email="reader@test.com")
        assert narrator.name == "New Reader"
        assert narrator.registered_via_event == self.event_code
        assert narrator.passphrase is not None

    def test_missing_name_shows_error(self):
        resp = self.client.post("/register/event/", {
            "code": "VALIDEVENT", "name": "", "email": "reader@test.com"
        })
        assert resp.status_code == 200
        assert b"Name and email are required" in resp.content

    def test_expired_event_code_rejected(self):
        self.event_code.expires_at = timezone.now() - timedelta(hours=1)
        self.event_code.save()
        resp = self.client.post("/register/event/", {
            "code": "VALIDEVENT", "name": "Test", "email": "t@t.com"
        })
        assert b"Invalid or expired" in resp.content

    def test_inactive_event_code_rejected(self):
        self.event_code.active = False
        self.event_code.save()
        resp = self.client.post("/register/event/", {
            "code": "VALIDEVENT", "name": "Test", "email": "t@t.com"
        })
        assert b"Invalid or expired" in resp.content

    def test_get_shows_form(self):
        resp = self.client.get("/register/event/")
        assert resp.status_code == 200
