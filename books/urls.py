from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    path("<str:book_id>/", views.playback, name="playback"),
    path("<str:book_id>/<uuid:recording_id>/", views.playback, name="playback_specific"),
]

portal_urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("preflight/<str:book_id>/", views.preflight, name="preflight"),
    path("record/<str:book_id>/", views.record, name="record"),
    path("upload/<str:book_id>/", views.upload_recording, name="upload"),
]
