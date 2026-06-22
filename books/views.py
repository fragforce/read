from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from .models import Book, Narrator, Recording


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


@narrator_required
def dashboard(request):
    narrator = request.narrator
    my_recordings = Recording.objects.filter(narrator=narrator).select_related("book")

    recorded_book_ids = set(my_recordings.values_list("book_id", flat=True))

    available_books = Book.objects.exclude(id__in=recorded_book_ids)

    books_with_availability = []
    for book in available_books:
        recording_count = book.recordings.count()
        if book.max_narrators is not None and recording_count >= book.max_narrators:
            continue
        books_with_availability.append({
            "book": book,
            "recording_count": recording_count,
        })

    return render(request, "books/dashboard.html", {
        "narrator": narrator,
        "my_recordings": my_recordings,
        "available_books": books_with_availability,
    })


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
            return redirect("portal:record", book_id=book.id)

        error = "Please confirm all items before continuing."

    return render(request, "books/preflight.html", {
        "book": book,
        "checklist_items": checklist_items,
        "error": error,
    })


@narrator_required
def record(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, "books/record.html", {"book": book})
