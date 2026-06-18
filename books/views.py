from django.http import Http404
from django.shortcuts import render, get_object_or_404

from .models import Book, Recording


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
