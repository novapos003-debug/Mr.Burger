import json

from fastapi import WebSocket


class PedidoWebSocketManager:
    """Broadcast de eventos de pedidos a todos los dispositivos conectados
    (cocina, caja, meseros). Regla del cliente: la cocina debe ver los tickets
    en el instante en que el mesero los envía."""

    def __init__(self) -> None:
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def broadcast(self, event: dict) -> None:
        data = json.dumps(event, default=str)
        for conn in list(self.connections):
            try:
                await conn.send_text(data)
            except Exception:
                self.disconnect(conn)


ws_manager = PedidoWebSocketManager()