from django.urls import re_path

from src.genre_ai.consumers import GenreAIConsumer

websocket_urlpatterns = [
    re_path(r"^ws/genre-ai/(?P<task_id>[0-9a-fA-F-]+)/?$", GenreAIConsumer.as_asgi()),
]
