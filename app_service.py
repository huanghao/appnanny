import os

import psutil

from logging_config import logger
from port_utils import find_available_port
from config import active_config as config
from app_state_manager import AppStateManager
from app_launcher import AppLauncher


class AppService:
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.state_manager = AppStateManager(
            os.path.join(storage_path, config.METADATA_FILE), storage_path
        )
        self.app_launcher = AppLauncher(storage_path)

        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def setup_app_logging(self, app_dir, app_name):
        """Setup rotating log files for app stdout and stderr"""
        log_dir = os.path.join(app_dir, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        stdout_log = os.path.join(log_dir, f"{app_name}_stdout.log")
        stderr_log = os.path.join(log_dir, f"{app_name}_stderr.log")

        return stdout_log, stderr_log

    def launch_app(self, app_name, app_type, repo, path, env_vars, preferred_port=None):
        """Launch a new application instance"""
        result = self.app_launcher.launch(
            app_name, app_type, repo, path, env_vars, preferred_port
        )
        if not result:
            return None

        port, process = result
        self.state_manager.add_running_app(
            app_name, process, port
        )  # PID handling inside state_manager
        return port

    def stop_app(self, app_name):
        """Stop a running application"""
        app_meta = self.state_manager.get_app_metadata(app_name)
        if not app_meta:
            logger.error(f"App '{app_name}' not found in metadata")
            return False

        if not self.state_manager.is_app_running(app_name):
            logger.error(f"App '{app_name}' is not running")
            return False

        process = self.state_manager.get_app_process(app_name)
        try:
            logger.info(
                f"Sending terminate signal to app '{app_name}' (PID: {process.pid})"
            )
            process.terminate()

            try:
                # Wait for process to terminate using psutil
                process.wait(timeout=5)
                logger.info(f"App '{app_name}' terminated gracefully")
            except psutil.TimeoutExpired:
                logger.warning(
                    f"App '{app_name}' did not terminate gracefully, forcing kill"
                )
                process.kill()
                logger.info(f"App '{app_name}' killed")

            self.state_manager.remove_running_app(app_name)
            return True

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error stopping app '{app_name}': {str(e)}", exc_info=True)
            # Clean up state even if process is already gone
            self.state_manager.remove_running_app(app_name)
            return False

    def restart_app(self, app_name):
        """Restart an application"""
        # First stop the app
        if not self.stop_app(app_name):
            logger.error(f"Failed to stop app '{app_name}' during restart")
            return None

        # Get metadata for relaunch
        app_meta = self.state_manager.get_app_metadata(app_name)
        if not app_meta:
            logger.error(f"App '{app_name}' not found in metadata during restart")
            return None

        # Relaunch with same configuration
        port = self.launch_app(
            app_name,
            app_meta["type"],
            app_meta["repo"],
            app_meta["path"],
            app_meta.get("env", {}),
        )

        if port:
            self.state_manager.update_app_status(app_name, True, port)
        return port

    def update_access_time(self, app_name):
        """Update last access time for an app"""
        return self.state_manager.update_access_time(app_name)

    def list_apps(self):
        """Get information about all apps"""
        all_info = {}
        for am in self.state_manager.get_all_metadata():
            app_info = {
                "type": am["type"],
                "repo": am["repo"],
                "path": am["path"],
                "email": am["email"],
                "running": self.state_manager.is_app_running(am["name"]),
                "port": am.get("port"),
                "uptime": 0,
            }

            if app_info["running"]:
                uptime = self.state_manager.get_app_uptime(
                    am["name"]
                )  # New method needed
                if uptime:
                    app_info["uptime"] = int(uptime)

            all_info[am["name"]] = app_info

        return all_info

    def create_app(self, app_name, app_type, repo, path, email, env_vars=None):
        """Create and start a new application"""
        env_vars = env_vars or {}

        # Get a new port for the app
        port = find_available_port()
        if not port:
            logger.error("No available ports")
            return None

        # Create app metadata
        app_data = {
            "name": app_name,
            "type": app_type,
            "repo": repo,
            "path": path,
            "email": email,
            "env": env_vars,
            "port": port,
            "is_active": False,
            "last_start_time": 0,
        }
        self.state_manager.add_app_metadata(app_data)

        # Launch the app with the assigned port
        launch_port = self.launch_app(app_name, app_type, repo, path, env_vars, port)
        if launch_port:
            self.state_manager.update_app_status(app_name, True)
            return launch_port
        return None

    def start_app(self, app_name):
        """Start an application"""
        # Don't start if already running
        if self.state_manager.is_app_running(app_name):  # New method needed
            logger.warning(f"App '{app_name}' is already running")
            return self.state_manager.get_app_port(app_name)  # New method needed

        # Find app metadata
        app_meta = self.state_manager.get_app_metadata(app_name)
        if not app_meta:
            logger.error(f"App '{app_name}' not found in metadata")
            return None

        # Launch the app with preferred port from metadata
        preferred_port = app_meta.get("port")
        port = self.launch_app(
            app_name,
            app_meta["type"],
            app_meta["repo"],
            app_meta["path"],
            app_meta.get("env", {}),
            preferred_port,
        )

        if port and port != preferred_port:
            self.state_manager.update_app_status(app_name, True, port)

        return port
