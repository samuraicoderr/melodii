import logging
from urllib.parse import urlsplit
from uuid import uuid4

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from celery import current_app
from django.conf import settings

from src.common.serializers import EmptySerializer
from src.lib.django.views_mixin import ViewSetHelperMixin
from src.genre_ai.services import GenreAIService
from src.genre_ai.tasks import classify_genre_task

logger = logging.getLogger(__name__)


def _ensure_celery_ready() -> tuple[bool, str]:
    broker_url = str(getattr(settings, "BROKER_URL", ""))
    if broker_url.startswith("memory://"):
        return False, "Celery broker is set to memory://. Start Redis and set REDIS_URL."

    try:
        responses = current_app.control.ping(timeout=5.0)
    except Exception:
        return False, "Celery worker is unavailable. Start a Celery worker process."

    if not responses:
        return False, "No Celery workers responded. Start a Celery worker process."

    return True, ""


def _build_websocket_url(request, task_id: str) -> str:
    host = request.get_host()
    if not host:
        parsed = urlsplit(str(getattr(settings, "SITE_URL", "")))
        host = parsed.netloc

    proto = "wss" if request.is_secure() or request.META.get("HTTP_X_FORWARDED_PROTO", "").lower() == "https" else "ws"
    return f"{proto}://{host}/ws/genre-ai/{task_id}/"


class GenreAIViewset(ViewSetHelperMixin, viewsets.GenericViewSet):
    serializers = {
        "default": EmptySerializer,
    }
    permissions = {
        "default": [AllowAny],
    }

    @action(
        detail=False,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def classify(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationError("File is required")

        try:
            celery_ready, celery_message = _ensure_celery_ready()
            if not celery_ready:
                return Response(
                    {"detail": celery_message},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            model_name = GenreAIService.resolve_model_name(request.data.get("model_name"))
            GenreAIService.validate_file(uploaded_file.name, uploaded_file.size)

            task_id = uuid4().hex
            storage_key = GenreAIService.save_uploaded_file(uploaded_file, task_id)
            try:
                classify_genre_task.apply_async(
                    args=[storage_key, uploaded_file.name, uploaded_file.size, model_name],
                    task_id=task_id,
                )
            except Exception:
                GenreAIService.cleanup_storage_file(storage_key)
                raise
        except ValidationError:
            raise
        except Exception:
            logger.exception("Genre classification could not be queued")
            return Response(
                {"detail": "Classification could not be queued. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        websocket_url = _build_websocket_url(request, task_id)
        return Response(
            {
                "success": True,
                "task_id": task_id,
                "status": "queued",
                "websocket_url": websocket_url,
            },
            status=status.HTTP_202_ACCEPTED,
        )
