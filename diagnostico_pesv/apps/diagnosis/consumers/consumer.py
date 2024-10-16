import json
from channels.generic.websocket import AsyncWebsocketConsumer


class DiagnosisConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "diagnosis"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # Notify the group about the change
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "websocket_diagnosis", "message": f"{text_data_json}"},
        )

    async def external_count(self, diagnosis):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "external_count",
                    "diagnosis_data": diagnosis["diagnosis_data"],
                }
            )
        )

    async def external_notification(self, notification):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "external_notification",
                    "notification_data": notification["notification_data"],
                }
            )
        )
