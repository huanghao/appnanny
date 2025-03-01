from abc import ABC, abstractmethod
import logging
import requests


class BaseProxy(ABC):
    def __init__(
        self, target_port: int, app_name: str, nanny_url: str = "http://localhost:5000"
    ):
        self.target_port = target_port
        self.app_name = app_name
        self.nanny_url = nanny_url
        self.heartbeat_url = f"{nanny_url}/heartbeat/{app_name}"
        self.logger = logging.getLogger(f"proxy_{app_name}")

    @abstractmethod
    def start(self, host: str = "0.0.0.0", port: int = None) -> None:
        """Start the proxy server"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the proxy server"""
        pass

    def _send_heartbeat(self) -> None:
        """Send heartbeat to nanny service"""
        try:
            requests.post(self.heartbeat_url, timeout=1)
        except Exception as e:
            self.logger.warning(f"Failed to send heartbeat: {e}")
