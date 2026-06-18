from django.urls import path
from . import views

app_name = "registration"

urlpatterns = [
    path("event/", views.register_event, name="event"),
    path("invite/<str:token>/", views.register_invite, name="invite"),
    path("welcome/", views.welcome, name="welcome"),
]

login_urlpatterns = [
    path("", views.login, name="login"),
    path("<str:passphrase>/", views.login_with_passphrase, name="login_passphrase"),
]
