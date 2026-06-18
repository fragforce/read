from django.urls import path
from . import views

app_name = "registration"

urlpatterns = [
    path("event/", views.register_event, name="event"),
    path("invite/<str:token>/", views.register_invite, name="invite"),
    path("login/", views.login, name="login"),
    path("welcome/", views.welcome, name="welcome"),
]
