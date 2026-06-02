import logging
import os
import shutil
import signal
import tempfile
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, List

from django.conf import settings
from django.core.files.storage import default_storage
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

    # Hard timeout (seconds) applied to each pipeline() call.
    # Covers both local-cache loads and remote HuggingFace downloads.
    MODEL_LOAD_TIMEOUT_SECONDS = 300

    @staticmethod
    @contextmanager
    def _pipeline_timeout(seconds: int):
        """
        Context manager that raises TimeoutError if the body does not complete
        within *seconds*. Uses SIGALRM on UNIX/Linux. On Windows the feature is
        unavailable, so this becomes a no-op and the pipeline runs without a
        Python-level timeout.
        """
        sigalrm = getattr(signal, "SIGALRM", None)
        if sigalrm is None:
            logger.warning(
                "SIGALRM not available on this platform; pipeline timeout disabled."
            )
            yield
            return

        def _handler(signum, frame):
            raise TimeoutError(
                f"pipeline() did not complete within {seconds} seconds"
            )

        old_handler = signal.signal(sigalrm, _handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)  # cancel any pending alarm
            signal.signal(sigalrm, old_handler)  # restore previous handler

    @staticmethod
    @lru_cache(maxsize=1)
    def get_classifier(model_name: str, cache_dir: str):
        try:
            from transformers import pipeline
        except ImportError as exc:
            logger.exception("Transformers not installed")
            raise ValidationError("Model dependencies are missing") from exc

        # Tell the HuggingFace hub client to time out individual HTTP requests
        # so a stalled download surfaces as an error rather than a silent hang.
        os.environ.setdefault(
            "HF_HUB_DOWNLOAD_TIMEOUT",
            str(GenreAIService.MODEL_LOAD_TIMEOUT_SECONDS),
        )

        hf_token = GenreAIService.get_settings()["hf_token"]
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        # Check if model files exist locally (config.json and model weights)
        config_path = os.path.join(cache_dir, "config.json")
        model_weight_path = os.path.join(cache_dir, "model.safetensors")
        if not os.path.isfile(model_weight_path):
            model_weight_path = os.path.join(cache_dir, "pytorch_model.bin")

        model_files_exist = os.path.isfile(config_path) and os.path.isfile(model_weight_path)

        # Validate model files are readable and non-empty before attempting to load
        if model_files_exist:
            try:
                config_size = os.path.getsize(config_path)
                model_size = os.path.getsize(model_weight_path)
                if config_size == 0 or model_size == 0:
                    logger.warning(
                        "Cached model files are empty or invalid (config: %d bytes, model: %d bytes)",
                        config_size,
                        model_size,
                    )
                    raise OSError("Cached model files are empty")
            except (OSError, IOError) as exc:
                logger.warning(
                    "Cached genre model is corrupted or inaccessible at %s. Clearing local cache: %s",
                    cache_dir,
                    exc,
                    exc_info=True,
                )
                shutil.rmtree(cache_dir, ignore_errors=True)
                model_files_exist = False

        if model_files_exist:
            logger.info(
                "Loading genre classification model from local cache: %s",
                cache_dir,
            )
            try:
                with GenreAIService._pipeline_timeout(GenreAIService.MODEL_LOAD_TIMEOUT_SECONDS):
                    return pipeline(
                        "audio-classification",
                        model=cache_dir,
                        token=hf_token,
                        cache_dir=cache_dir,
                    )
            except TimeoutError:
                logger.error(
                    "Timed out loading genre model from local cache after %d seconds: %s",
                    GenreAIService.MODEL_LOAD_TIMEOUT_SECONDS,
                    cache_dir,
                )
                shutil.rmtree(cache_dir, ignore_errors=True)
                raise
            except Exception as exc:
                logger.warning(
                    "Cached genre model failed to load from %s. Clearing local cache and retrying: %s",
                    cache_dir,
                    exc,
                    exc_info=True,
                )
                shutil.rmtree(cache_dir, ignore_errors=True)
                model_to_load = model_name
        else:
            logger.info(
                "Model not found locally or cleared due to corruption. Loading from HuggingFace: %s",
                model_name,
            )
            model_to_load = model_name

        logger.info(
            "Loading genre classification model from HuggingFace (timeout: %ds): %s",
            GenreAIService.MODEL_LOAD_TIMEOUT_SECONDS,
            model_to_load,
        )
        try:
            with GenreAIService._pipeline_timeout(GenreAIService.MODEL_LOAD_TIMEOUT_SECONDS):
                return pipeline(
                    "audio-classification",
                    model=model_to_load,
                    token=hf_token,
                    cache_dir=cache_dir,
                )
        except TimeoutError:
            logger.error(
                "Timed out loading genre model from HuggingFace after %d seconds: %s",
                GenreAIService.MODEL_LOAD_TIMEOUT_SECONDS,
                model_to_load,
            )
            raise

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
        GenreAIService._ensure_audio_processing_dependencies()
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
        storage_key = os.path.join("genre_ai", "uploads", f"{task_id}{safe_ext}")

        if default_storage.exists(storage_key):
            default_storage.delete(storage_key)

        saved_name = default_storage.save(storage_key, uploaded_file)
        return saved_name

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
    def cleanup_storage_file(storage_key: str | None) -> None:
        if not storage_key:
            return
        try:
            if default_storage.exists(storage_key):
                default_storage.delete(storage_key)
        except Exception:
            logger.warning("Failed to remove storage file: %s", storage_key, exc_info=True)

    @staticmethod
    def classify_storage_file(
        storage_key: str,
        model_name: str | None = None,
        log_callback: Callable[[str], None] | None = None,
    ) -> dict:
        local_path = None
        try:
            local_path = GenreAIService._download_storage_file_to_temp(storage_key)
            return GenreAIService._classify_path(
                local_path,
                filename=os.path.basename(storage_key),
                file_size_bytes=os.path.getsize(local_path),
                model_name=model_name,
                log_callback=log_callback,
            )
        finally:
            GenreAIService.cleanup_temp_file(local_path)

    @staticmethod
    def _download_storage_file_to_temp(storage_key: str) -> str:
        _, ext = os.path.splitext(storage_key)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".audio")
        temp_file.close()

        def _log_storage_context(message: str) -> None:
            backend_name = getattr(default_storage, "__class__", type(default_storage)).__name__
            bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
            endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
            logger.warning(
                "%s | storage_key=%s backend=%s bucket=%s endpoint=%s",
                message,
                storage_key,
                backend_name,
                bucket_name,
                endpoint,
            )

        try:
            with default_storage.open(storage_key, "rb") as source, open(temp_file.name, "wb") as dest:
                shutil.copyfileobj(source, dest)
            return temp_file.name
        except FileNotFoundError as exc:
            _log_storage_context("default_storage file not found")
            GenreAIService.cleanup_temp_file(temp_file.name)
            return GenreAIService._download_storage_file_to_temp_boto3(storage_key)
        except Exception:
            GenreAIService.cleanup_temp_file(temp_file.name)
            raise

    @staticmethod
    def _download_storage_file_to_temp_boto3(storage_key: str) -> str:
        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            logger.exception("boto3 is required for S3 fallback")
            raise RuntimeError("boto3 is required for direct S3 fallback") from exc

        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        if not bucket:
            raise RuntimeError("AWS_STORAGE_BUCKET_NAME is not configured for direct S3 fallback")

        endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        region_name = getattr(settings, "AWS_S3_REGION_NAME", None)
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
        addressing_style = getattr(settings, "AWS_S3_ADDRESSING_STYLE", None)

        config = Config(
            s3={"addressing_style": addressing_style or "auto"},
            region_name=region_name,
        )

        kwargs = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": config,
        }
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url

        client = boto3.client("s3", **{k: v for k, v in kwargs.items() if v is not None})
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(storage_key)[1] or ".audio")
        temp_file.close()
        try:
            logger.info(
                "Attempting direct S3 fallback download: bucket=%s key=%s endpoint=%s",
                bucket,
                storage_key,
                endpoint_url,
            )
            response = client.get_object(Bucket=bucket, Key=storage_key)
            with response["Body"] as body, open(temp_file.name, "wb") as dest:
                shutil.copyfileobj(body, dest)
            return temp_file.name
        except Exception:
            GenreAIService.cleanup_temp_file(temp_file.name)
            logger.exception("Direct S3 fallback download failed for %s", storage_key)
            raise

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
    def _ensure_audio_processing_dependencies() -> None:
        try:
            import librosa  # noqa: F401
            import soundfile  # noqa: F401
        except ImportError as exc:
            logger.exception("Audio processing dependencies are missing")
            raise ValidationError(
                "Audio processing requires librosa and soundfile. Install the Python dependencies."
            ) from exc

    @staticmethod
    def _clip_audio(file_path: str, seconds: int) -> str:
        try:
            import librosa
            import soundfile as sf
        except ImportError as exc:
            logger.exception("Audio processing dependencies are missing")
            raise ValidationError(
                "Audio processing requires librosa and soundfile. Install the Python dependencies."
            ) from exc

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.close()

        try:
            audio, sr = librosa.load(
                file_path,
                sr=16000,
                mono=True,
                duration=seconds,
            )
            if audio.size == 0:
                raise ValidationError("Audio file could not be processed")

            sf.write(temp_file.name, audio, sr, subtype="PCM_16")
            return temp_file.name
        except Exception as exc:
            GenreAIService.cleanup_temp_file(temp_file.name)
            logger.exception("Audio processing failed")
            raise ValidationError("Audio file could not be processed") from exc
