"""
ASGI config for melodii project.

Handles both HTTP (via Django WSGI adapter) and WebSocket (via Django Channels).
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")

django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

from src.genre_ai.routing import websocket_urlpatterns as genre_ai_websocket_urlpatterns
from src.notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns

django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            URLRouter(notification_websocket_urlpatterns + genre_ai_websocket_urlpatterns)
        ),
    }
)
