import logging
import os
import shutil
import tempfile
from functools import lru_cache
from typing import Dict, List

from django.conf import settings
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class GenreAIService:
    @staticmethod
    def get_settings() -> Dict[str, object]:
        return {
            "default_model": getattr(
                settings,
                "GENRE_AI_DEFAULT_MODEL",
                "dima806/music_genres_classification",
            ),
            "hf_token": getattr(settings, "GENRE_AI_HF_TOKEN", None),
            "max_file_size_mb": getattr(settings, "GENRE_AI_MAX_FILE_SIZE_MB", 30),
            "allowed_extensions": set(
                ext.lower()
                for ext in getattr(
                    settings,
                    "GENRE_AI_ALLOWED_EXTENSIONS",
                    [".mp3", ".wav", ".ogg", ".flac", ".m4a"],
                )
            ),
            "top_k": max(1, int(getattr(settings, "GENRE_AI_TOP_K", 5))),
        }

    @staticmethod
    def resolve_model_name(model_name: str | None) -> str:
        settings_map = GenreAIService.get_settings()
        default_model = settings_map["default_model"]
        chosen = model_name or default_model

        if chosen != default_model:
            raise ValidationError(
                "This model will be available in V2 after training and integration"
            )

        return chosen

    @staticmethod
    @lru_cache(maxsize=1)
    def get_classifier(model_name: str):
        try:
            from transformers import pipeline
        except ImportError as exc:
            logger.exception("Transformers not installed")
            raise ValidationError("Model dependencies are missing") from exc

        settings_map = GenreAIService.get_settings()
        hf_token = settings_map["hf_token"]

        logger.info("Loading genre classification model: %s", model_name)
        return pipeline(
            "audio-classification",
            model=model_name,
            token=hf_token,
        )

    @staticmethod
    def validate_file(filename: str, file_size_bytes: int) -> None:
        settings_map = GenreAIService.get_settings()
        max_bytes = int(settings_map["max_file_size_mb"]) * 1024 * 1024

        if file_size_bytes > max_bytes:
            raise ValidationError("File exceeds 30MB limit")

        _, ext = os.path.splitext(filename)
        if ext.lower() not in settings_map["allowed_extensions"]:
            raise ValidationError("Unsupported file type")

    @staticmethod
    def classify_uploaded_file(uploaded_file, model_name: str | None) -> dict:
        model_to_use = GenreAIService.resolve_model_name(model_name)
        GenreAIService.validate_file(uploaded_file.name, uploaded_file.size)

        temp_path = None
        try:
            temp_path = GenreAIService._write_temp_file(uploaded_file)
            return GenreAIService._classify_path(
                temp_path,
                filename=uploaded_file.name,
                file_size_bytes=uploaded_file.size,
                model_name=model_to_use,
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    @staticmethod
    def classify_file_path(file_path: str, model_name: str | None = None) -> dict:
        if not os.path.isfile(file_path):
            raise ValidationError("File not found")

        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        model_to_use = GenreAIService.resolve_model_name(model_name)

        GenreAIService.validate_file(filename, file_size)
        return GenreAIService._classify_path(
            file_path,
            filename=filename,
            file_size_bytes=file_size,
            model_name=model_to_use,
        )

    @staticmethod
    def _classify_path(
        file_path: str,
        filename: str,
        file_size_bytes: int,
        model_name: str,
    ) -> dict:
        GenreAIService._ensure_ffmpeg_available()
        settings_map = GenreAIService.get_settings()
        classifier = GenreAIService.get_classifier(model_name)
        raw_predictions = classifier(file_path, top_k=settings_map["top_k"])

        if not raw_predictions:
            raise ValidationError("No predictions returned from model")

        predictions: List[dict] = [
            {"label": item["label"], "score": float(item["score"])}
            for item in raw_predictions
        ]

        return {
            "success": True,
            "model_used": model_name,
            "filename": filename,
            "top_prediction": predictions[0],
            "predictions": predictions,
        }

    @staticmethod
    def _write_temp_file(uploaded_file) -> str:
        _, ext = os.path.splitext(uploaded_file.name)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            with temp_file as tmp_handle:
                shutil.copyfileobj(uploaded_file, tmp_handle)
            return temp_file.name
        except Exception:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise

    @staticmethod
    def _ensure_ffmpeg_available() -> None:
        if shutil.which("ffmpeg") is None:
            raise ValidationError(
                "ffmpeg is required to process audio files. Install it and ensure it is on your PATH."
            )
