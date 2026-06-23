from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    path("audio/<uuid:recording_id>/", views.serve_recording, name="serve_recording"),
    path("play/<str:book_id>/", views.playback, name="playback"),
    path("play/<str:book_id>/<uuid:recording_id>/", views.playback, name="playback_specific"),
]

portal_urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="profile"),
    path("preflight/<str:book_id>/", views.preflight, name="preflight"),
    path("record/<str:book_id>/", views.record, name="record"),
    path("upload/<str:book_id>/", views.upload_recording, name="upload"),
    path("recording/<uuid:recording_id>/", views.recording_detail, name="recording_detail"),
    path("recording/<uuid:recording_id>/flag/", views.flag_recording, name="flag_recording"),
]
