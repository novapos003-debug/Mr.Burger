import asyncio
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
        if not self.connections:
            return
        data = json.dumps(event, default=str)

        async def _enviar(conn: WebSocket):
            try:
                await asyncio.wait_for(conn.send_text(data), timeout=2.5)
            except Exception:
                self.disconnect(conn)

        # Enviar en paralelo a todos los clientes para que uno lento o con Wi-Fi inestable no demore a los demás
        await asyncio.gather(*[_enviar(c) for c in list(self.connections)], return_exceptions=True)


ws_manager = PedidoWebSocketManager()