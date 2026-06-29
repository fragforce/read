from django.test import TestCase

from books.models import Narrator
from registration.models import EventCode, InviteLink


class EventCodeModelTest(TestCase):
    def test_is_valid_active(self):
        ec = EventCode.objects.create(code="VALID", active=True)
        assert ec.is_valid() is True

    def test_is_valid_inactive(self):
        ec = EventCode.objects.create(code="INACTIVE", active=False)
        assert ec.is_valid() is False

    def test_str(self):
        ec = EventCode.objects.create(code="ABC123", label="Test Event")
        assert "Test Event" in str(ec)
        assert "ABC123" in str(ec)

    def test_auto_generates_code_when_empty(self):
        ec = EventCode(label="Auto Code")
        ec.save()
        assert ec.code != ""


class InviteLinkModelTest(TestCase):
    def test_is_valid_fresh(self):
        invite = InviteLink.objects.create(token="fresh", label="Fresh")
        assert invite.is_valid() is True

    def test_is_valid_used(self):
        invite = InviteLink.objects.create(token="used", label="Used")
        invite.used = True
        assert invite.is_valid() is False

    def test_mark_used(self):
        narrator = Narrator.objects.create(
            name="Mark User", email="mark@test.com", passphrase="mark-phrase"
        )
        invite = InviteLink.objects.create(token="mark-test", label="Mark Test")
        invite.mark_used(narrator)
        invite.refresh_from_db()
        assert invite.used is True
        assert invite.narrator == narrator
        assert invite.used_at is not None

    def test_str(self):
        invite = InviteLink.objects.create(token="str-test", label="Str Label")
        assert "active" in str(invite)
        invite.used = True
        invite.save()
        assert "used" in str(invite)

    def test_auto_generates_token_when_empty(self):
        invite = InviteLink(label="Auto Token")
        invite.save()
        assert invite.token != ""
