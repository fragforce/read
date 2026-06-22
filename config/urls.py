import ipaddress

from django.contrib import admin
from django.db import connection
from django.http import Http404, JsonResponse
from django.urls import path, include
from django.views.generic import TemplateView

from books.urls import portal_urlpatterns
from registration.urls import login_urlpatterns

PRIVATE_NETWORKS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)


def healthz(request):
    ip = ipaddress.ip_address(request.META["REMOTE_ADDR"])
    if not any(ip in net for net in PRIVATE_NETWORKS):
        raise Http404

    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=503)

urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("b/", include("books.urls")),
    path("portal/", include((portal_urlpatterns, "portal"))),
    path("login/", include((login_urlpatterns, "login"))),
    path("register/", include("registration.urls")),
]
