from django.test import Client, TestCase

from books.models import Book, Narrator, QRCode, Recording, RecordingStatus
from books.qr import generate_label_png, generate_qr_png, generate_qr_svg


class QRRedirectTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="QR User", email="qr@test.com", passphrase="qr-phrase"
        )
        self.book = Book.objects.create(title="QR Book", slug="qr-book", author="Author")
        self.recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        self.qr = QRCode.objects.create(
            book=self.book, recording=self.recording, label_text="QR Test"
        )

    def test_redirect_with_recording(self):
        resp = self.client.get(f"/code/{self.qr.short_code}/")
        assert resp.status_code == 302
        assert f"/b/play/{self.book.id}/{self.recording.id}/" in resp.url

    def test_redirect_without_recording(self):
        qr = QRCode.objects.create(book=self.book, recording=None, label_text="No Rec")
        resp = self.client.get(f"/code/{qr.short_code}/")
        assert resp.status_code == 302
        assert f"/b/play/{self.book.id}/" in resp.url

    def test_invalid_short_code_404(self):
        resp = self.client.get("/code/nonexist/")
        assert resp.status_code == 404


class QRImageViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.narrator = Narrator.objects.create(
            name="QR Img User", email="qrimg@test.com", passphrase="qrimg-phrase"
        )
        self.book = Book.objects.create(title="QR Img Book", slug="qr-img-book", author="Author")
        self.recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        self.qr = QRCode.objects.create(
            book=self.book, recording=self.recording, label_text="Image Test"
        )

    def test_qr_png_returns_image(self):
        resp = self.client.get(f"/b/qr/{self.qr.id}.png")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/png"
        assert resp["Cache-Control"] == "no-store"
        assert resp.content[:4] == b"\x89PNG"

    def test_qr_svg_returns_svg(self):
        resp = self.client.get(f"/b/qr/{self.qr.id}.svg")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/svg+xml"
        assert b"<svg" in resp.content or b"<?xml" in resp.content

    def test_qr_label_returns_png(self):
        resp = self.client.get(f"/b/qr/{self.qr.id}/label.png")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "image/png"
        assert resp.content[:4] == b"\x89PNG"

    def test_qr_sheet_returns_page(self):
        resp = self.client.get(f"/b/qr/sheet/{self.book.id}/")
        assert resp.status_code == 200

    def test_qr_sheet_404_when_no_codes(self):
        book = Book.objects.create(title="Empty", slug="empty-book", author="Author")
        resp = self.client.get(f"/b/qr/sheet/{book.id}/")
        assert resp.status_code == 404


class QRGenerationTest(TestCase):
    def test_generate_qr_png(self):
        img = generate_qr_png("https://example.com/test")
        assert img is not None

    def test_generate_qr_svg(self):
        img = generate_qr_svg("https://example.com/test")
        assert img is not None

    def test_generate_label_png_with_password(self):
        buf = generate_label_png(
            "https://example.com/test", "My Book Title", "Narrator Name", password="test-pw"
        )
        assert buf.getvalue()[:4] == b"\x89PNG"

    def test_generate_label_png_without_password(self):
        buf = generate_label_png(
            "https://example.com/test", "My Book Title", "Narrator Name"
        )
        assert buf.getvalue()[:4] == b"\x89PNG"
