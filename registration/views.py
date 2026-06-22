from django.shortcuts import render, redirect
from django.http import Http404
from django.views.decorators.http import require_http_methods, require_GET

from books.models import Narrator
from .models import EventCode, InviteLink
from .wordlist import generate_passphrase


@require_http_methods(["GET", "POST"])
def register_event(request):
    error = None

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()

        event_code = EventCode.objects.filter(code=code).first()
        if not event_code or not event_code.is_valid():
            error = "Invalid or expired event code."
        elif not name or not email:
            error = "Name and email are required."
        else:
            passphrase = generate_passphrase()
            narrator = Narrator.objects.create(
                name=name, email=email, passphrase=passphrase, registered_via_event=event_code
            )
            request.session["narrator_id"] = str(narrator.id)
            return redirect("registration:welcome")

    return render(request, "registration/event.html", {"error": error})


@require_http_methods(["GET", "POST"])
def register_invite(request, token):
    invite = InviteLink.objects.filter(token=token).first()
    if not invite or not invite.is_valid():
        raise Http404("This invite link is invalid or has already been used.")

    error = None

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()

        if not name or not email:
            error = "Name and email are required."
        else:
            passphrase = generate_passphrase()
            narrator = Narrator.objects.create(name=name, email=email, passphrase=passphrase)
            invite.mark_used(narrator)
            request.session["narrator_id"] = str(narrator.id)
            return redirect("registration:welcome")

    return render(request, "registration/invite.html", {"invite": invite, "error": error})


@require_http_methods(["GET", "POST"])
def login(request):
    error = None

    if request.method == "POST":
        passphrase = request.POST.get("passphrase", "").strip().lower()
        narrator = Narrator.objects.filter(passphrase=passphrase).first()
        if not narrator:
            error = "Invalid passphrase."
        else:
            request.session["narrator_id"] = str(narrator.id)
            return redirect("registration:welcome")

    return render(request, "registration/login.html", {"error": error})


@require_GET
def login_with_passphrase(request, passphrase):
    narrator = Narrator.objects.filter(passphrase=passphrase.lower()).first()
    if not narrator:
        return render(request, "registration/login.html", {"error": "Invalid passphrase."})
    request.session["narrator_id"] = str(narrator.id)
    return redirect("registration:welcome")


@require_GET
def logout(request):
    request.session.pop("narrator_id", None)
    return redirect("home")


@require_GET
def welcome(request):
    narrator_id = request.session.get("narrator_id")
    if not narrator_id:
        return redirect("registration:event")

    narrator = Narrator.objects.filter(id=narrator_id).first()
    if not narrator:
        return redirect("registration:event")

    return render(request, "registration/welcome.html", {"narrator": narrator})
