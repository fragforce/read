from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from books.models import Narrator

from .models import EventCode, InviteLink
from .wordlist import generate_passphrase

RATE_LIMIT_MESSAGE = "Too many attempts. Please try again later."
WELCOME_URL = "registration:welcome"


def _check_lockout(request, attempts_key, lockout_key):
    lockout_until = request.session.get(lockout_key)
    if lockout_until and timezone.now().timestamp() < lockout_until:
        return True
    if lockout_until:
        request.session.pop(lockout_key, None)
        request.session[attempts_key] = 0
    return False


def _record_failed_attempt(request, attempts_key, lockout_key, lockout_duration):
    attempts = request.session.get(attempts_key, 0) + 1
    request.session[attempts_key] = attempts
    if attempts >= settings.LOGIN_MAX_ATTEMPTS:
        request.session[lockout_key] = timezone.now().timestamp() + lockout_duration
        return True
    return False


def _clear_lockout(request, attempts_key, lockout_key):
    request.session.pop(attempts_key, None)
    request.session.pop(lockout_key, None)


def _handle_event_registration(request):
    if _check_lockout(request, "event_reg_attempts", "event_reg_lockout"):
        return RATE_LIMIT_MESSAGE

    code = request.POST.get("code", "").strip()
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()

    event_code = EventCode.objects.filter(code=code).first()
    if not event_code or not event_code.is_valid():
        locked_out = _record_failed_attempt(
            request, "event_reg_attempts", "event_reg_lockout",
            settings.EVENT_LOGIN_LOCKOUT_SECONDS,
        )
        return RATE_LIMIT_MESSAGE if locked_out else "Invalid or expired event code."

    if not name or not email:
        return "Name and email are required."

    _clear_lockout(request, "event_reg_attempts", "event_reg_lockout")
    passphrase = generate_passphrase()
    narrator = Narrator.objects.create(
        name=name, email=email, passphrase=passphrase, registered_via_event=event_code
    )
    request.session["narrator_id"] = str(narrator.id)
    return None


@require_http_methods(["GET", "POST"])
def register_event(request):
    unlock_code = request.GET.get("unlock", "")
    if unlock_code and settings.LOGIN_UNLOCK_CODE and unlock_code == settings.LOGIN_UNLOCK_CODE:
        _clear_lockout(request, "event_reg_attempts", "event_reg_lockout")

    error = None
    if request.method == "POST":
        error = _handle_event_registration(request)
        if error is None:
            return redirect(WELCOME_URL)

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
            return redirect(WELCOME_URL)

    return render(request, "registration/invite.html", {"invite": invite, "error": error})


@require_http_methods(["GET", "POST"])
def login(request):
    error = None

    if request.method == "POST":
        if _check_lockout(request, "login_attempts", "login_lockout"):
            error = RATE_LIMIT_MESSAGE
        else:
            passphrase = request.POST.get("passphrase", "").strip().lower()
            narrator = Narrator.objects.filter(passphrase=passphrase).first()
            if not narrator:
                locked_out = _record_failed_attempt(
                    request, "login_attempts", "login_lockout",
                    settings.LOGIN_LOCKOUT_SECONDS,
                )
                error = RATE_LIMIT_MESSAGE if locked_out else "Invalid passphrase."
            else:
                _clear_lockout(request, "login_attempts", "login_lockout")
                request.session["narrator_id"] = str(narrator.id)
                return redirect(WELCOME_URL)

    return render(request, "registration/login.html", {"error": error})


@require_GET
def login_with_passphrase(request, passphrase):
    narrator = Narrator.objects.filter(passphrase=passphrase.lower()).first()
    if not narrator:
        return render(request, "registration/login.html", {"error": "Invalid passphrase."})
    request.session["narrator_id"] = str(narrator.id)
    return redirect(WELCOME_URL)


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
