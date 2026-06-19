from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from books.urls import portal_urlpatterns
from registration.urls import login_urlpatterns

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("b/", include("books.urls")),
    path("portal/", include((portal_urlpatterns, "portal"))),
    path("login/", include((login_urlpatterns, "login"))),
    path("register/", include("registration.urls")),
]
