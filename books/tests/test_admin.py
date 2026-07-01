import os
import shutil

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from books.admin import BookAdmin, NarratorAdmin, QRCodeAdmin, RecordingAdmin
from books.models import Book, Narrator, QRCode, Recording, RecordingStatus


class BookAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = BookAdmin(Book, self.site)
        self.factory = RequestFactory()
        self.book = Book.objects.create(title="Admin Book", slug="admin-book", author="Author")

    def test_qr_sheet_link(self):
        result = self.admin.qr_sheet_link(self.book)
        assert f"/b/qr/sheet/{self.book.id}/" in result
        assert "Print" in result

    def test_get_exclude_on_create(self):
        request = self.factory.get("/admin/books/book/add/")
        assert self.admin.get_exclude(request, obj=None) == ("id",)

    def test_get_exclude_on_edit(self):
        request = self.factory.get(f"/admin/books/book/{self.book.id}/change/")
        assert self.admin.get_exclude(request, obj=self.book) == ()

    def test_get_fields_on_create(self):
        request = self.factory.get("/admin/books/book/add/")
        fields = self.admin.get_fields(request, obj=None)
        assert "id" not in fields
        assert "title" in fields

    def test_get_fields_on_edit(self):
        request = self.factory.get(f"/admin/books/book/{self.book.id}/change/")
        fields = self.admin.get_fields(request, obj=self.book)
        assert fields[0] == "id"
        assert "title" in fields


class NarratorAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = NarratorAdmin(Narrator, self.site)
        self.factory = RequestFactory()
        self.narrator = Narrator.objects.create(
            name="Admin Narrator", email="admin@test.com", passphrase="admin-test-phrase"
        )

    def test_has_passphrase_true(self):
        assert self.admin.has_passphrase(self.narrator) is True

    def test_has_passphrase_false(self):
        self.narrator.passphrase = ""
        assert self.admin.has_passphrase(self.narrator) is False

    def test_passphrase_display_with_pk(self):
        result = self.admin.passphrase_display(self.narrator)
        assert "admin-test-phrase" in result
        assert "Generate new passphrase" in result

    def test_passphrase_display_without_pk(self):
        narrator = Narrator(name="New", email="new@test.com", passphrase="test")
        narrator.pk = None
        result = self.admin.passphrase_display(narrator)
        assert result == "test"

    def test_response_change_generate_passphrase(self):
        from unittest.mock import patch

        user = User.objects.create_superuser("admin", "admin@test.com", "password")
        request = self.factory.post(
            f"/admin/books/narrator/{self.narrator.id}/change/",
            {"_generate_passphrase": "1"},
        )
        request.user = user

        with patch.object(self.admin, "message_user"):
            response = self.admin.response_change(request, self.narrator)
        assert response.status_code == 302

        self.narrator.refresh_from_db()
        assert self.narrator.passphrase != "admin-test-phrase"


class RecordingAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = RecordingAdmin(Recording, self.site)
        self.factory = RequestFactory()
        self.narrator = Narrator.objects.create(
            name="Rec Admin", email="recadmin@test.com", passphrase="rec-admin-phrase"
        )
        self.book = Book.objects.create(title="Rec Admin Book", slug="rec-admin", author="Author")
        for d in ("recordings", "processing", "finalized"):
            os.makedirs(os.path.join(settings.MEDIA_ROOT, d), exist_ok=True)

    def tearDown(self):
        for d in ("recordings", "processing", "finalized"):
            path = os.path.join(settings.MEDIA_ROOT, d)
            if os.path.exists(path):
                shutil.rmtree(path)

    def test_retry_failed_recordings(self):
        from unittest.mock import patch

        recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.FAILED
        )
        file_path = os.path.join(settings.MEDIA_ROOT, "recordings", f"{recording.id}.webm")
        with open(file_path, "wb") as f:
            f.write(b"audio")
        recording.audio_file.name = f"recordings/{recording.id}.webm"
        recording.save(update_fields=["audio_file"])

        request = self.factory.post("/admin/books/recording/")
        request.user = User.objects.create_superuser("admin2", "a2@test.com", "pw")

        with patch("books.processing.spawn_remux") as mock_spawn, \
             patch.object(self.admin, "message_user"):
            self.admin.retry_failed_recordings(request, Recording.objects.filter(id=recording.id))

        recording.refresh_from_db()
        assert recording.status == RecordingStatus.PENDING
        mock_spawn.assert_called_once_with(recording.id)


class QRCodeAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = QRCodeAdmin(QRCode, self.site)
        self.book = Book.objects.create(title="QR Admin Book", slug="qr-admin", author="Author")
        self.narrator = Narrator.objects.create(
            name="QR Narrator", email="qr@test.com", passphrase="qr-admin-phrase"
        )
        self.recording = Recording.objects.create(
            book=self.book, narrator=self.narrator, status=RecordingStatus.READY
        )
        self.qr = QRCode.objects.create(
            book=self.book, recording=self.recording, label_text="Test QR"
        )

    def test_qr_links(self):
        result = self.admin.qr_links(self.qr)
        assert f"/b/qr/{self.qr.id}.png" in result
        assert f"/b/qr/{self.qr.id}.svg" in result
        assert f"/b/qr/{self.qr.id}/label.png" in result
