import logging
from datetime import datetime, timezone

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

from src.genre_ai.services import GenreAIService

logger = logging.getLogger(__name__)

EVENT_CACHE_TTL_SECONDS = 60 * 30
MAX_CACHED_EVENTS = 200


def task_group_name(task_id: str) -> str:
    return f"genre_ai_{task_id}"


def task_events_cache_key(task_id: str) -> str:
    return f"genre_ai:task_events:{task_id}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_cached_task_events(task_id: str) -> list[dict]:
    events = cache.get(task_events_cache_key(task_id))
    return events if isinstance(events, list) else []


def _cache_event(task_id: str, event: dict) -> None:
    events = get_cached_task_events(task_id)
    events.append(event)
    cache.set(
        task_events_cache_key(task_id),
        events[-MAX_CACHED_EVENTS:],
        timeout=EVENT_CACHE_TTL_SECONDS,
    )


def send_task_event(task_id: str, event_type: str, payload: dict | None = None) -> None:
    event = {
        "type": event_type,
        "task_id": task_id,
        "timestamp": _now_iso(),
        **(payload or {}),
    }
    _cache_event(task_id, event)

    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        task_group_name(task_id),
        {"type": "genre_ai.message", "data": event},
    )


def send_log(task_id: str, message: str, level: str = "info") -> None:
    send_task_event(task_id, "log", {"message": message, "level": level})


def _validation_message(exc: ValidationError) -> str:
    detail = getattr(exc, "detail", None)
    if isinstance(detail, list) and detail:
        return str(detail[0])
    if isinstance(detail, dict):
        return " ".join(str(value) for value in detail.values())
    return str(exc)


@shared_task(bind=True, name="genre_ai.classify")
def classify_genre_task(
    self,
    file_path: str,
    filename: str,
    file_size_bytes: int,
    model_name: str,
) -> dict:
    task_id = self.request.id
    send_log(task_id, "Queued for processing")

    try:
        send_log(task_id, f"Received {filename}")
        send_log(task_id, "Validating file")
        GenreAIService.validate_file(filename, file_size_bytes)

        result = GenreAIService.classify_file_path(
            file_path,
            model_name=model_name,
            log_callback=lambda message: send_log(task_id, message),
        )

        top = result["top_prediction"]
        send_log(
            task_id,
            f"Top prediction: {top['label']} ({top['score']:.3f})",
        )
        send_task_event(task_id, "result", {"payload": result})
        send_task_event(task_id, "done", {"status": "completed"})
        return result
    except ValidationError as exc:
        message = _validation_message(exc)
        send_log(task_id, message, level="error")
        send_task_event(task_id, "error", {"message": message})
        send_task_event(task_id, "done", {"status": "failed"})
        logger.warning("Genre AI validation error: %s", message)
        raise
    except Exception:
        message = "Classification failed. Please try again later."
        send_log(task_id, message, level="error")
        send_task_event(task_id, "error", {"message": message})
        send_task_event(task_id, "done", {"status": "failed"})
        logger.exception("Genre AI task failed")
        raise
    finally:
        GenreAIService.cleanup_temp_file(file_path)
