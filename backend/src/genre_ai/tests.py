import io
import wave
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase


class GenreAiClassifyTests(TestCase):
    def _make_wav_file(self) -> SimpleUploadedFile:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(b"\x00\x00" * 1600)
        buffer.seek(0)
        return SimpleUploadedFile("sample.wav", buffer.read(), content_type="audio/wav")

    @patch("src.genre_ai.views._ensure_celery_ready", return_value=(True, ""))
    def test_rejects_invalid_extension(self, _mock_celery_ready):
        upload = SimpleUploadedFile("track.txt", b"not audio", content_type="text/plain")
        response = self.client.post(
            "/api/v1/genre-ai/classify/",
            data={"file": upload},
        )
        self.assertEqual(response.status_code, 400)

    @patch("src.genre_ai.views._ensure_celery_ready", return_value=(True, ""))
    def test_missing_file_returns_validation_error(self, _mock_celery_ready):
        response = self.client.post("/api/v1/genre-ai/classify/")
        self.assertIn(response.status_code, {400, 422})

    @patch("src.genre_ai.views.classify_genre_task.apply_async")
    @patch("src.genre_ai.views.GenreAIService.save_uploaded_file")
    @patch("src.genre_ai.views._ensure_celery_ready", return_value=(True, ""))
    def test_success_response_shape(self, _mock_celery_ready, mock_save_uploaded_file, mock_apply_async):
        mock_save_uploaded_file.return_value = "genre_ai/uploads/test_task.wav"
        upload = self._make_wav_file()

        response = self.client.post(
            "/api/v1/genre-ai/classify/",
            data={"file": upload},
            HTTP_X_FORWARDED_PROTO="https",
        )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["status"], "queued")
        self.assertIn("/ws/genre-ai/", payload["websocket_url"])
        self.assertTrue(payload["websocket_url"].startswith("wss://"))
        mock_save_uploaded_file.assert_called_once()
        mock_apply_async.assert_called_once()
