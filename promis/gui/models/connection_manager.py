from fastapi import WebSocket, WebSocketDisconnect

from promis.gui.models.line import Line
from promis.gui.models.location_type_table import LocationTypeEntry
from promis.gui.models.marker import Marker
from promis.gui.models.polygon import Polygon


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_entity(self, entity: Marker | Line | Polygon, websocket: WebSocket):
        try:
            await websocket.send_json(entity.model_dump_json())
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)

    async def send_personal_loc_type(self, loc_type: LocationTypeEntry, websocket: WebSocket):
        try:
            await websocket.send_json(loc_type.model_dump_json())
        except WebSocketDisconnect:
            self.active_connections.remove(websocket)

    async def broadcast_entity(self, entity: Marker | Line | Polygon):
        for connection in self.active_connections:
            await self.send_personal_entity(entity, connection)

    async def broadcast_loc_type(self, loc_type: LocationTypeEntry):
        for connection in self.active_connections:
            await self.send_personal_loc_type(loc_type, connection)
