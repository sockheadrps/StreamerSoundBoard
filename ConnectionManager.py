from fastapi import WebSocket
from typing import List


class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    async def disconnect_user(self, websocket: WebSocket):
        self.connections.remove(websocket)
