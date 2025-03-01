from flask import Flask, Response, request
import requests
from werkzeug.wsgi import get_input_stream

from base_proxy import BaseProxy


class FlaskProxy(BaseProxy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = Flask(f"proxy_{self.app_name}")
        self.setup_routes()

    def setup_routes(self):
        @self.app.route(
            "/",
            defaults={"path": ""},
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        )
        @self.app.route(
            "/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        )
        def proxy(path):
            return self._handle_request(path)

    def _handle_request(self, path):
        target_url = f"http://localhost:{self.target_port}/{path}"

        try:
            resp = requests.request(
                method=request.method,
                url=target_url,
                headers=self._forward_headers(request.headers),
                data=get_input_stream(request.environ).read(),
                params=request.args,
                cookies=request.cookies,
                stream=True,
            )

            if resp.status_code < 400:
                self._send_heartbeat()

            return Response(
                resp.iter_content(chunk_size=10 * 1024),
                status=resp.status_code,
                headers=self._forward_headers(resp.headers),
            )

        except Exception as e:
            self.logger.error(f"Proxy error: {e}")
            return Response(f"Proxy error: {str(e)}", status=502)

    def start(self, host="0.0.0.0", port=None):
        if port is None:
            port = self.target_port + 1000
        self.app.run(host=host, port=port)

    def stop(self):
        # Flask development server doesn't provide a clean way to stop
        pass
