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

	def test_rejects_invalid_extension(self):
		upload = SimpleUploadedFile("track.txt", b"not audio", content_type="text/plain")
		response = self.client.post(
			"/api/v1/genre-ai/classify/",
			data={"file": upload},
		)
		self.assertEqual(response.status_code, 400)

	def test_missing_file_returns_validation_error(self):
		response = self.client.post("/api/v1/genre-ai/classify/")
		self.assertIn(response.status_code, {400, 422})

	@patch("src.genre_ai.services.GenreAIService.get_classifier")
	def test_success_response_shape(self, mock_classifier):
		mock_classifier.return_value = lambda _path, top_k=5: [
			{"label": "Hip-Hop", "score": 0.91},
			{"label": "Reggae", "score": 0.05},
		]

		response = self.client.post(
			"/api/v1/genre-ai/classify/",
			data={"file": self._make_wav_file()},
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertTrue(payload["success"])
		self.assertEqual(payload["top_prediction"]["label"], "Hip-Hop")
		self.assertEqual(len(payload["predictions"]), 2)
