from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Attestation, Book, Narrator, Recording


@require_http_methods(["GET", "POST"])
def playback(request, book_id, recording_id=None):
    book = get_object_or_404(Book, id=book_id)

    if recording_id:
        recording = get_object_or_404(Recording, id=recording_id, book=book)
    else:
        recording = book.recordings.order_by("?").first()
        if not recording:
            raise Http404("No recordings available for this book.")

    if not book.public_domain:
        qr_code = book.qr_codes.filter(recording=recording).first() or book.qr_codes.first()
        password_required = bool(qr_code and qr_code.password)
        password_valid = False

        if password_required:
            submitted = request.POST.get("password", "")
            if submitted and submitted == qr_code.password:
                password_valid = True
                request.session[f"book_{book_id}_unlocked"] = True
            elif request.session.get(f"book_{book_id}_unlocked"):
                password_valid = True
    else:
        password_required = False
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
