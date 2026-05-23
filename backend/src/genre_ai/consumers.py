import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from src.genre_ai.tasks import get_cached_task_events, task_group_name

logger = logging.getLogger(__name__)


class GenreAIConsumer(AsyncJsonWebsocketConsumer):
    task_id: str | None = None
    group_name: str | None = None

    async def connect(self):
        self.task_id = self.scope.get("url_route", {}).get("kwargs", {}).get("task_id")
        if not self.task_id:
            await self.close(code=4000)
            return

        self.group_name = task_group_name(self.task_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._replay_cached_events()

        logger.debug("Genre AI websocket connected: task_id=%s", self.task_id)

    async def disconnect(self, close_code: int):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.debug(
            "Genre AI websocket disconnected: task_id=%s code=%s",
            self.task_id,
            close_code,
        )

    async def receive_json(self, content: dict, **kwargs):
        msg_type = content.get("type")
        if msg_type == "ping":
            await self.send_json({"type": "pong"})
            return

        await self.send_json(
            {
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
            }
        )

    async def genre_ai_message(self, event: dict):
        await self.send_json(event.get("data", {}))

    async def _replay_cached_events(self):
        if not self.task_id:
            return
        for event in get_cached_task_events(self.task_id):
            await self.send_json(event)
