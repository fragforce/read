from django.test import Client, TestCase


class HealthzTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_healthz_from_localhost(self):
        resp = self.client.get("/healthz/", REMOTE_ADDR="127.0.0.1")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_healthz_from_private_network(self):
        resp = self.client.get("/healthz/", REMOTE_ADDR="10.0.0.1")
        assert resp.status_code == 200

    def test_healthz_from_public_ip_returns_404(self):
        resp = self.client.get("/healthz/", REMOTE_ADDR="8.8.8.8")
        assert resp.status_code == 404

    def test_healthz_blocked_when_proxied(self):
        resp = self.client.get(
            "/healthz/", REMOTE_ADDR="172.18.0.3", HTTP_X_FORWARDED_PROTO="https"
        )
        assert resp.status_code == 404
