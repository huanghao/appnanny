import asyncio
import websockets

from base_proxy import BaseProxy


class WebSocketProxy(BaseProxy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = None
        self.loop = None

    async def _handle_connection(self, websocket, path):
        try:
            async with websockets.connect(
                f"ws://localhost:{self.target_port}{path}"
            ) as ws:
                # Bidirectional relay
                while True:
                    message = await websocket.recv()
                    await ws.send(message)
                    response = await ws.recv()
                    await websocket.send(response)
                    self._send_heartbeat()
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")

    def start(self, host="0.0.0.0", port=None):
        if port is None:
            port = self.target_port + 1000

        async def start_server():
            self.server = await websockets.serve(self._handle_connection, host, port)
            await self.server.wait_closed()

        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(start_server())
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket proxy: {e}")
        finally:
            if self.loop:
                self.loop.close()

    def stop(self):
        if self.server:
            self.server.close()
        if self.loop and self.loop.is_running():
            self.loop.stop()
