import logging
import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, List

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
            "model_cache_dir": getattr(settings, "GENRE_AI_MODEL_CACHE_DIR"),
            "clip_seconds": max(1, int(getattr(settings, "GENRE_AI_CLIP_SECONDS", 120))),
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
    def get_classifier(model_name: str, cache_dir: str):
        try:
            from transformers import pipeline
        except ImportError as exc:
            logger.exception("Transformers not installed")
            raise ValidationError("Model dependencies are missing") from exc

        hf_token = GenreAIService.get_settings()["hf_token"]
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        logger.info(
            "Loading genre classification model: %s (cache=%s)",
            model_name,
            cache_dir,
        )
        return pipeline(
            "audio-classification",
            model=model_name,
            token=hf_token,
            cache_dir=cache_dir,
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
    def classify_uploaded_file(
        uploaded_file,
        model_name: str | None,
        log_callback: Callable[[str], None] | None = None,
    ) -> dict:
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
                log_callback=log_callback,
            )
        finally:
            GenreAIService.cleanup_temp_file(temp_path)

    @staticmethod
    def classify_file_path(
        file_path: str,
        model_name: str | None = None,
        log_callback: Callable[[str], None] | None = None,
    ) -> dict:
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
            log_callback=log_callback,
        )

    @staticmethod
    def _classify_path(
        file_path: str,
        filename: str,
        file_size_bytes: int,
        model_name: str,
        log_callback: Callable[[str], None] | None = None,
    ) -> dict:
        def log_step(message: str) -> None:
            if log_callback:
                log_callback(message)

        log_step("Checking audio processing tools")
        GenreAIService._ensure_ffmpeg_available()
        settings_map = GenreAIService.get_settings()
        cache_dir = str(settings_map["model_cache_dir"])

        clipped_path = None
        try:
            log_step(f"Preparing first {settings_map['clip_seconds']} seconds of audio")
            clipped_path = GenreAIService._clip_audio(
                file_path,
                seconds=int(settings_map["clip_seconds"]),
            )

            log_step("Loading model from persistent cache")
            classifier = GenreAIService.get_classifier(model_name, cache_dir)

            log_step("Running genre classification")
            raw_predictions = classifier(clipped_path, top_k=settings_map["top_k"])
        finally:
            GenreAIService.cleanup_temp_file(clipped_path)

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
    def save_uploaded_file(uploaded_file, task_id: str) -> str:
        _, ext = os.path.splitext(uploaded_file.name)
        safe_ext = ext.lower() or ".audio"
        jobs_dir = Path(tempfile.gettempdir()) / "melodii_genre_ai_jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        temp_path = jobs_dir / f"{task_id}{safe_ext}"

        with temp_path.open("wb") as tmp_handle:
            for chunk in uploaded_file.chunks():
                tmp_handle.write(chunk)

        return str(temp_path)

    @staticmethod
    def cleanup_temp_file(file_path: str | None) -> None:
        if not file_path:
            return
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except OSError:
            logger.warning("Failed to remove temp file: %s", file_path, exc_info=True)

    @staticmethod
    def _write_temp_file(uploaded_file) -> str:
        _, ext = os.path.splitext(uploaded_file.name)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            with temp_file as tmp_handle:
                shutil.copyfileobj(uploaded_file, tmp_handle)
            return temp_file.name
        except Exception:
            GenreAIService.cleanup_temp_file(temp_file.name)
            raise

    @staticmethod
    def _ensure_ffmpeg_available() -> None:
        if shutil.which("ffmpeg") is None:
            raise ValidationError(
                "ffmpeg is required to process audio files. Install it and ensure it is on your PATH."
            )

    @staticmethod
    def _clip_audio(file_path: str, seconds: int) -> str:
        _, ext = os.path.splitext(file_path)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".audio")
        temp_file.close()

        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            file_path,
            "-t",
            str(seconds),
            "-c",
            "copy",
            temp_file.name,
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            return temp_file.name
        except subprocess.CalledProcessError:
            GenreAIService.cleanup_temp_file(temp_file.name)
            fallback_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            fallback_path.close()
            fallback_command = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                file_path,
                "-t",
                str(seconds),
                "-ac",
                "1",
                "-ar",
                "16000",
                fallback_path.name,
            ]
            try:
                subprocess.run(fallback_command, check=True, capture_output=True, text=True)
                return fallback_path.name
            except subprocess.CalledProcessError as exc:
                GenreAIService.cleanup_temp_file(fallback_path.name)
                logger.exception("ffmpeg failed to prepare audio clip")
                raise ValidationError("Audio file could not be processed") from exc
