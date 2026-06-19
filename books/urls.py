from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    path("<str:book_id>/", views.playback, name="playback"),
    path("<str:book_id>/<uuid:recording_id>/", views.playback, name="playback_specific"),
]

portal_urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
