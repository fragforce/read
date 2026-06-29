from django.test import Client, TestCase

from books.models import Narrator


class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Login User", email="login@test.com", passphrase="valid-phrase"
        )

    def test_wrong_passphrase_shows_error(self):
        resp = self.client.post("/login/", {"passphrase": "wrong"})
        assert resp.status_code == 200
        assert b"Invalid passphrase" in resp.content

    def test_lockout_after_5_attempts(self):
        for _ in range(5):
            self.client.post("/login/", {"passphrase": "wrong"})
        resp = self.client.post("/login/", {"passphrase": "wrong"})
        assert b"Too many attempts" in resp.content

    def test_valid_login_clears_lockout(self):
        for _ in range(3):
            self.client.post("/login/", {"passphrase": "wrong"})
        resp = self.client.post("/login/", {"passphrase": "valid-phrase"}, follow=True)
        assert resp.status_code == 200
        assert self.client.session["narrator_id"] == str(self.narrator.id)

    def test_login_is_case_insensitive(self):
        resp = self.client.post("/login/", {"passphrase": "VALID-PHRASE"}, follow=True)
        assert resp.status_code == 200
        assert self.client.session["narrator_id"] == str(self.narrator.id)

    def test_login_get_shows_form(self):
        resp = self.client.get("/login/")
        assert resp.status_code == 200


class LoginWithPassphraseURLTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="URL Login", email="url@test.com", passphrase="url-login-phrase"
        )

    def test_valid_passphrase_url_logs_in(self):
        resp = self.client.get("/login/url-login-phrase/", follow=True)
        assert resp.status_code == 200
        assert self.client.session["narrator_id"] == str(self.narrator.id)

    def test_invalid_passphrase_url_shows_error(self):
        resp = self.client.get("/login/wrong-phrase/")
        assert resp.status_code == 200
        assert b"Invalid passphrase" in resp.content

    def test_case_insensitive_login(self):
        resp = self.client.get("/login/URL-LOGIN-PHRASE/", follow=True)
        assert resp.status_code == 200
        assert self.client.session["narrator_id"] == str(self.narrator.id)


class LogoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Logout Test", email="logout@test.com", passphrase="logout-phrase"
        )
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()

    def test_logout_clears_session(self):
        resp = self.client.get("/register/logout/", follow=True)
        assert resp.status_code == 200
        assert "narrator_id" not in self.client.session


class WelcomeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="Welcome Test", email="welcome@test.com", passphrase="welcome-phrase"
        )

    def test_welcome_with_session(self):
        session = self.client.session
        session["narrator_id"] = str(self.narrator.id)
        session.save()
        resp = self.client.get("/register/welcome/")
        assert resp.status_code == 200

    def test_welcome_without_session_redirects(self):
        resp = self.client.get("/register/welcome/")
        assert resp.status_code == 302

    def test_welcome_with_invalid_narrator_redirects(self):
        session = self.client.session
        session["narrator_id"] = "00000000-0000-0000-0000-000000000000"
        session.save()
        resp = self.client.get("/register/welcome/")
        assert resp.status_code == 302
