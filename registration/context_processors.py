from books.models import Narrator


def narrator(request):
    narrator_id = request.session.get("narrator_id")
    if narrator_id:
        narrator = Narrator.objects.filter(id=narrator_id).first()
        if narrator:
            return {"narrator_name": narrator.name}
    return {}
