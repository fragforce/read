from django.test import TestCase

from books.models import (
    Book,
    Narrator,
    Recording,
    generate_book_id,
    generate_qr_password,
    generate_qr_short_code,
)


class BookModelTest(TestCase):
    def test_generate_book_id_length(self):
        book_id = generate_book_id()
        assert len(book_id) == 12

    def test_generate_book_id_alphabet(self):
        allowed = set("23456789abcdefghjkmnpqrstuvwxyz")
        book_id = generate_book_id()
        assert all(c in allowed for c in book_id)

    def test_book_auto_generates_id(self):
        book = Book.objects.create(title="Auto ID", slug="auto-id", author="Author")
        assert len(book.id) == 12

    def test_book_str(self):
        book = Book.objects.create(title="Str Book", slug="str-book", author="Author")
        assert str(book) == "Str Book"


class NarratorModelTest(TestCase):
    def test_narrator_str(self):
        narrator = Narrator.objects.create(
            name="Str Narrator", email="str@test.com", passphrase="str-phrase"
        )
        assert str(narrator) == "Str Narrator"


class RecordingModelTest(TestCase):
    def test_duration_formatted(self):
        narrator = Narrator.objects.create(
            name="Model User", email="model@test.com", passphrase="model-phrase"
        )
        book = Book.objects.create(title="Model Book", slug="model-book", author="Author")
        recording = Recording.objects.create(
            book=book, narrator=narrator, duration_seconds=125
        )
        assert recording.duration_formatted == "2:05"

    def test_duration_formatted_none(self):
        narrator = Narrator.objects.create(
            name="Model User2", email="model2@test.com", passphrase="model2-phrase"
        )
        book = Book.objects.create(title="Model Book2", slug="model-book2", author="Author")
        recording = Recording.objects.create(
            book=book, narrator=narrator, duration_seconds=None
        )
        assert recording.duration_formatted is None

    def test_recording_str(self):
        narrator = Narrator.objects.create(
            name="Rec Narrator", email="rec@test.com", passphrase="rec-phrase"
        )
        book = Book.objects.create(title="Rec Book", slug="rec-book", author="Author")
        recording = Recording.objects.create(book=book, narrator=narrator)
        assert str(recording) == "Rec Book - Rec Narrator"


class QRCodeModelTest(TestCase):
    def test_generate_qr_short_code_length(self):
        code = generate_qr_short_code()
        assert len(code) == 8

    def test_generate_qr_password_format(self):
        pw = generate_qr_password()
        parts = pw.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4
