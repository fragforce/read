from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from registration.admin import EventCodeAdmin, InviteLinkAdmin
from registration.models import EventCode, InviteLink


class EventCodeAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = EventCodeAdmin(EventCode, self.site)
        self.factory = RequestFactory()

    def test_get_exclude_on_create(self):
        request = self.factory.get("/admin/registration/eventcode/add/")
        assert self.admin.get_exclude(request, obj=None) == ("code",)

    def test_get_exclude_on_edit(self):
        event_code = EventCode.objects.create(label="Test Event")
        request = self.factory.get(f"/admin/registration/eventcode/{event_code.id}/change/")
        assert self.admin.get_exclude(request, obj=event_code) is None


class InviteLinkAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = InviteLinkAdmin(InviteLink, self.site)
        self.factory = RequestFactory()

    def test_get_exclude_on_create(self):
        request = self.factory.get("/admin/registration/invitelink/add/")
        assert self.admin.get_exclude(request, obj=None) == ("token", "used", "used_at", "narrator")

    def test_get_exclude_on_edit(self):
        invite = InviteLink.objects.create(label="Test Invite")
        request = self.factory.get(f"/admin/registration/invitelink/{invite.id}/change/")
        assert self.admin.get_exclude(request, obj=invite) is None
