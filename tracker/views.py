import base64

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from .models import Counter

# ------------------------------------------------------------
# 1×1 прозрачный GIF в формате bytes.
# Мы возвращаем его в ответ, чтобы трекинг работал как “пиксель”:
# <img src=".../t.gif?..."> НЕ требует CORS и работает везде.
# ------------------------------------------------------------
_GIF_1x1 = base64.b64decode("R0lGODlhAQABAPAAAAAAAAAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==")


def _clean(value: str, max_len: int) -> str:
    """
    Небольшая защита от “мусора”:
    - превращаем None в пустую строку
    - обрезаем пробелы
    - ограничиваем длину, чтобы не тащить гигантские значения в БД
    """
    value = (value or "").strip()
    if not value:
        return ""
    return value[:max_len]


@require_GET
def pixel(request):
    """
    ПИКСЕЛЬ-ТРЕКЕР

    Пример:
    GET /t.gif?e=between_view&src=ai-chat-pages&k=SECRET

    Логика:
    1) проверяем ключ k (если ключ задан в settings.TRACKER_KEY)
    2) если ключ верный — увеличиваем счётчик события (event + src)
    3) в любом случае возвращаем 1×1 gif (чтобы не “палить” отказ атакующему)
    """
    # k — простой секретный ключ против накрутки
    key = request.GET.get("k", "")

    # Если ключ настроен (не пустой) и не совпал — ничего не считаем,
    # но GIF всё равно возвращаем (не даём понять, что ключ неверный).
    if settings.TRACKER_KEY and key != settings.TRACKER_KEY:
        resp = HttpResponse(_GIF_1x1, content_type="image/gif")
        # Запрещаем кэширование, чтобы каждый запрос реально доходил до сервера
        resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp

    # e — имя события (обязательно). src — источник/проект (необязательно).
    event = _clean(request.GET.get("e", ""), 120)
    src = _clean(request.GET.get("src", ""), 120)

    if event:
        # transaction.atomic(): делаем операцию “цельной” (атомарной).
        # Это важно, когда запросы приходят параллельно.
        with transaction.atomic():
            # get_or_create: либо находим строку счётчика, либо создаём новую.
            obj, created = Counter.objects.get_or_create(event=event, src=src)

            if created:
                # Если строка новая — просто записываем count = 1
                obj.count = 1
                obj.save(update_fields=["count"])
            else:
                # Если строка уже есть — увеличиваем count на 1.
                # F("count") + 1 делает инкремент прямо на уровне SQL,
                # что безопаснее при параллельных запросах.
                Counter.objects.filter(pk=obj.pk).update(count=F("count") + 1)

    # Возвращаем наш GIF-пиксель
    resp = HttpResponse(_GIF_1x1, content_type="image/gif")
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp


@require_GET
def stats(request):
    """
    СТАТИСТИКА (JSON)

    Пример:
    GET /api/stats?src=ai-chat-pages&k=SECRET

    Возвращает:
    {
      "items": [
        {"event": "...", "src": "...", "count": 123, "updated_at": "..."},
        ...
      ]
    }
    """
    key = request.GET.get("k", "")
    # Для API статистики — уже честно запрещаем доступ при неверном ключе.
    if settings.TRACKER_KEY and key != settings.TRACKER_KEY:
        return JsonResponse({"detail": "Forbidden"}, status=403)

    src = _clean(request.GET.get("src", ""), 120)

    # Берём все счётчики и сортируем по убыванию count
    qs = Counter.objects.all().order_by("-count")

    # Если передали src — фильтруем по нему
    if src:
        qs = qs.filter(src=src)

    # Отдаём не больше 500 строк, чтобы случайно не уронить страницу
    data = [
        {
            "event": c.event,
            "src": c.src,
            "count": c.count,
            "updated_at": c.updated_at.isoformat(),
        }
        for c in qs[:500]
    ]
    return JsonResponse({"items": data})
