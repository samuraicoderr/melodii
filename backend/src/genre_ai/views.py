import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from src.common.serializers import EmptySerializer
from src.lib.django.views_mixin import ViewSetHelperMixin
from src.genre_ai.services import GenreAIService

logger = logging.getLogger(__name__)


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
            payload = GenreAIService.classify_uploaded_file(
                uploaded_file,
                request.data.get("model_name"),
            )
        except ValidationError:
            raise
        except Exception:
            logger.exception("Genre classification failed")
            return Response(
                {"detail": "Classification failed. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(payload, status=status.HTTP_200_OK)
