import io
import logging
import os
import re

from django.db.models import Count
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

logger = logging.getLogger(__name__)

from .models import Attestation, Book, Narrator, QRCode, Recording, RecordingStatus
from .processing import spawn_remux
from .qr import generate_label_png, generate_qr_png, generate_qr_svg


@require_http_methods(["GET", "POST"])
def playback(request, book_id, recording_id=None):
    book = get_object_or_404(Book, id=book_id)

    if recording_id:
        recording = get_object_or_404(
            Recording, id=recording_id, book=book, status=RecordingStatus.READY
        )
    else:
        recording = book.recordings.filter(status=RecordingStatus.READY).order_by("?").first()
        if not recording:
            raise Http404("No recordings available for this book.")

    password_required = book.qr_codes.exclude(password="").exists()
    password_valid = False

    if password_required:
        if request.session.get(f"book_{book_id}_unlocked"):
            password_valid = True
        else:
            submitted = request.POST.get("password", "").strip().lower()
            if submitted and book.qr_codes.filter(password=submitted).exists():
                password_valid = True
                request.session[f"book_{book_id}_unlocked"] = True
    else:
        password_valid = True

    return render(request, "books/playback.html", {
        "book": book,
        "recording": recording,
        "password_required": password_required,
        "password_valid": password_valid,
    })


def narrator_required(view_func):
    def wrapper(request, *args, **kwargs):
        narrator_id = request.session.get("narrator_id")
        if not narrator_id:
            return redirect("login:login")
        narrator = Narrator.objects.filter(id=narrator_id).first()
        if not narrator:
            request.session.pop("narrator_id", None)
            return redirect("login:login")
        request.narrator = narrator
        return view_func(request, *args, **kwargs)
    return wrapper


@require_GET
@narrator_required
def dashboard(request):
    narrator = request.narrator
    my_recordings = Recording.objects.filter(narrator=narrator).select_related("book")

    unflagged_book_ids = set(
        my_recordings.filter(flagged_for_review=False).values_list("book_id", flat=True)
    )

    available_books = (
        Book.objects.exclude(id__in=unflagged_book_ids)
        .annotate(recording_count=Count("recordings"))
    )

    books_with_availability = []
    for book in available_books:
        if book.max_narrators is not None and book.recording_count >= book.max_narrators:
            continue
        books_with_availability.append({
            "book": book,
            "recording_count": book.recording_count,
        })

    return render(request, "books/dashboard.html", {
        "narrator": narrator,
        "my_recordings": my_recordings,
        "available_books": books_with_availability,
    })


@require_http_methods(["GET", "POST"])
@narrator_required
def preflight(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    checklist_items = [
        {"key": "quiet_room", "label": "I'm in a quiet room with minimal background noise"},
        {"key": "mic_connected", "label": "My microphone is connected and working"},
        {"key": "water", "label": "I have water nearby"},
        {"key": "phone_silenced", "label": "My phone is silenced"},
    ]

    if not book.public_domain or not book.full_text:
        checklist_items.append(
            {"key": "physical_book", "label": "I have the physical book ready to read from"}
        )

    error = None
    if request.method == "POST":
        for item in checklist_items:
            item["checked"] = bool(request.POST.get(item["key"]))

        all_checked = all(item["checked"] for item in checklist_items)
        if all_checked:
            request.session[f"preflight_{book.id}"] = True
            return redirect("portal:record", book_id=book.id)

        error = "Please confirm all items before continuing."

    return render(request, "books/preflight.html", {
        "book": book,
        "checklist_items": checklist_items,
        "error": error,
    })


@require_GET
@narrator_required
def record(request, book_id):
    if not request.session.get(f"preflight_{book_id}"):
        return redirect("portal:preflight", book_id=book_id)
    book = get_object_or_404(Book, id=book_id)
    return render(request, "books/record.html", {"book": book, "narrator": request.narrator})


@require_POST
@narrator_required
def upload_recording(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    narrator = request.narrator

    audio_file = request.FILES.get("audio")
    if not audio_file:
        return JsonResponse({"error": "No audio file provided."}, status=400)

    if audio_file.content_type not in ("audio/webm", "audio/ogg", "audio/mp4", "audio/wav"):
        return JsonResponse({"error": "Unsupported audio format."}, status=400)

    duration = request.POST.get("duration")
    duration_seconds = int(float(duration)) if duration else None

    attestation_text = request.POST.get("attestation_text", "").strip()
    if not attestation_text:
        return JsonResponse({"error": "Attestation is required."}, status=400)

    try:
        recording = Recording.objects.create(
            book=book,
            narrator=narrator,
            audio_file=audio_file,
            duration_seconds=duration_seconds,
        )

        Attestation.objects.create(
            recording=recording,
            narrator=narrator,
            book=book,
            attestation_text=attestation_text,
        )
    except Exception:
        logger.exception("Failed to save recording for book=%s narrator=%s", book_id, narrator.id)
        return JsonResponse({
            "error": "Something went wrong saving your recording. Please let an admin know."
        }, status=500)

    spawn_remux(recording.id)

    request.session.pop(f"preflight_{book_id}", None)
    return JsonResponse({
        "id": str(recording.id),
        "redirect": f"/portal/recording/{recording.id}/",
    })


@require_GET
@narrator_required
def recording_detail(request, recording_id):
    recording = get_object_or_404(Recording, id=recording_id, narrator=request.narrator)
    return render(request, "books/recording_detail.html", {
        "recording": recording,
        "narrator": request.narrator,
    })


@require_POST
@narrator_required
def flag_recording(request, recording_id):
    recording = get_object_or_404(Recording, id=recording_id, narrator=request.narrator)

    reason = request.POST.get("reason", "").strip()
    if not reason:
        return render(request, "books/recording_detail.html", {
            "recording": recording,
            "narrator": request.narrator,
            "error": "Please provide a reason for flagging.",
        })

    recording.flagged_for_review = True
    recording.flag_reason = reason
    recording.save()

    return redirect("portal:recording_detail", recording_id=recording.id)


@require_http_methods(["GET", "POST"])
@narrator_required
def profile(request):
    narrator = request.narrator
    error = None
    success = False

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()

        if not name or not email:
            error = "Name and email are required."
        else:
            narrator.name = name
            narrator.email = email
            narrator.save()
            success = True

    return render(request, "books/profile.html", {
        "narrator": narrator,
        "error": error,
        "success": success,
    })


@require_GET
def serve_recording(request, recording_id):
    recording = get_object_or_404(Recording, id=recording_id)

    if recording.status == RecordingStatus.READY:
        path = recording.finalized_path
    else:
        narrator_id = request.session.get("narrator_id")
        if str(recording.narrator_id) != str(narrator_id):
            raise Http404
        path = recording.audio_file.path

    if not os.path.exists(path):
        raise Http404

    file_size = os.path.getsize(path)
    content_type = "audio/webm"

    range_header = request.META.get("HTTP_RANGE")
    if range_header:
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            f = open(path, "rb")
            f.seek(start)
            response = FileResponse(f, content_type=content_type, status=206)
            response["Content-Length"] = length
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Accept-Ranges"] = "bytes"
            return response

    response = FileResponse(open(path, "rb"), content_type=content_type)
    response["Content-Length"] = file_size
    response["Accept-Ranges"] = "bytes"
    return response


def _playback_url(request, qr_code):
    path = reverse("qr_redirect", kwargs={"short_code": qr_code.short_code})
    return request.build_absolute_uri(path)


@require_GET
def qr_redirect(request, short_code):
    qr_code = get_object_or_404(QRCode.objects.select_related("book", "recording"), short_code=short_code)
    if qr_code.recording:
        url = reverse("books:playback_specific", kwargs={"book_id": qr_code.book_id, "recording_id": qr_code.recording_id})
    else:
        url = reverse("books:playback", kwargs={"book_id": qr_code.book_id})
    return redirect(url)


@require_GET
def qr_png(request, qr_id):
    qr_code = get_object_or_404(QRCode.objects.select_related("book", "recording"), id=qr_id)
    url = _playback_url(request, qr_code)
    img = generate_qr_png(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type="image/png")
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def qr_svg(request, qr_id):
    qr_code = get_object_or_404(QRCode.objects.select_related("book", "recording"), id=qr_id)
    url = _playback_url(request, qr_code)
    img = generate_qr_svg(url)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type="image/svg+xml")
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def qr_label(request, qr_id):
    qr_code = get_object_or_404(QRCode.objects.select_related("book", "recording__narrator"), id=qr_id)
    url = _playback_url(request, qr_code)
    narrator_name = qr_code.recording.narrator.name if qr_code.recording else "Unknown"
    buf = generate_label_png(url, qr_code.book.title, narrator_name, password=qr_code.password or None)
    response = HttpResponse(buf.getvalue(), content_type="image/png")
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def qr_sheet(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    qr_codes = book.qr_codes.select_related("recording__narrator").all()
    if not qr_codes.exists():
        raise Http404("No QR codes for this book.")

    items = []
    for qr_code in qr_codes:
        url = _playback_url(request, qr_code)
        narrator_name = qr_code.recording.narrator.name if qr_code.recording else "Unknown"
        items.append({
            "qr_code": qr_code,
            "url": url,
            "narrator_name": narrator_name,
        })

    return render(request, "books/qr_sheet.html", {"book": book, "items": items})
