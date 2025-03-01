import os
import json
import time

import psutil
from dotenv import dotenv_values

from logging_config import logger
from pid_manager import PIDManager


class AppStateManager:
    def __init__(self, metadata_file, storage_path):
        """Initialize AppStateManager

        Args:
            metadata_file: Path to metadata JSON file
            storage_path: Base path for app storage
        """
        self.metadata_file = metadata_file
        self.storage_path = storage_path  # Add this line
        self._pid_manager = PIDManager(storage_path)  # Internal dependency
        self.running_apps = {}
        self.apps_metadata = []

        self.load_metadata()
        self._recover_running_state()

    def load_metadata(self):
        """Load apps metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r") as f:
                    self.apps_metadata = json.load(f)
            except json.JSONDecodeError:
                logger.error("Failed to load metadata file")
                self.apps_metadata = []

    def save_metadata(self):
        """Save apps metadata to file"""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.apps_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {str(e)}")

    def add_app_metadata(self, app_data):
        """Add new app to metadata"""
        self.apps_metadata.append(app_data)
        self.save_metadata()

    def update_app_status(self, app_name, is_active, port=None):
        """Update app status in metadata"""
        for am in self.apps_metadata:
            if am["name"] == app_name:
                am["is_active"] = is_active
                if port:
                    am["port"] = port
                am["last_start_time"] = (
                    time.time() if is_active else am.get("last_start_time", 0)
                )
                self.save_metadata()
                break

    def update_app_metadata(self, app_name, updates):
        """Update metadata for an app"""
        for am in self.apps_metadata:
            if am["name"] == app_name:
                am.update(updates)
                self.save_metadata()
                break

    def get_all_metadata(self):
        """Get list of all apps metadata

        Returns:
            list: List of dictionaries containing app metadata
        """
        return self.apps_metadata.copy()  # Return a copy to prevent direct modification

    # Runtime state operations (no save needed)
    def add_running_app(self, app_name, process, port):
        """Add a running app to runtime state"""
        self.running_apps[app_name] = {
            "process": process,
            "port": port,
            "start_time": time.time(),
            "last_access_time": time.time(),
        }
        # Save PID and update persistent state
        self._pid_manager.save_pid(app_name, process.pid)
        self.update_app_status(app_name, True, port)

    def remove_running_app(self, app_name):
        """Remove a running app from runtime state"""
        if app_name in self.running_apps:
            # Clean up PID file first
            self._pid_manager.remove_pid(app_name)
            del self.running_apps[app_name]
            # Update persistent state
            self.update_app_status(app_name, False)

    def get_app_metadata(self, app_name):
        """Get metadata for an app"""
        return next((am for am in self.apps_metadata if am["name"] == app_name), None)

    def update_access_time(self, app_name):
        """Update last access time for an app"""
        if app_name in self.running_apps:
            self.running_apps[app_name]["last_access_time"] = time.time()
            return True
        return False

    def get_app_uptime(self, app_name):
        """Get uptime for a running app

        Args:
            app_name: Name of the app

        Returns:
            float: Uptime in seconds, or None if app not running
        """
        if app_name in self.running_apps:
            return time.time() - self.running_apps[app_name]["start_time"]
        return None

    def is_app_running(self, app_name):
        """Check if an app is currently running

        Args:
            app_name: Name of the app

        Returns:
            bool: True if app is running, False otherwise
        """
        return app_name in self.running_apps

    def get_app_port(self, app_name):
        """Get the port number for a running app

        Args:
            app_name: Name of the app

        Returns:
            int: Port number, or None if app not running
        """
        if app_name in self.running_apps:
            return self.running_apps[app_name]["port"]
        return None

    def get_app_process(self, app_name):
        """Get the process object for a running app

        Args:
            app_name: Name of the app

        Returns:
            subprocess.Popen: Process object, or None if app not running
        """
        if app_name in self.running_apps:
            return self.running_apps[app_name]["process"]
        return None

    def _recover_running_state(self):
        """Recover running state from disk during initialization"""
        logger.info("Recovering running apps state from disk")
        for am in self.apps_metadata:
            app_name = am["name"]
            pid = self._pid_manager.get_pid(app_name)
            if pid and self._pid_manager.is_process_running(pid):
                try:
                    # Create psutil.Process object for the existing process
                    process = psutil.Process(pid)
                    logger.info(f"Found running app '{app_name}' with PID {pid}")
                    self.running_apps[app_name] = {
                        "process": process,  # Use psutil.Process instead of subprocess.Popen
                        "port": am["port"],
                        "start_time": process.create_time(),  # Get actual process start time
                        "last_access_time": time.time(),
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logger.warning(
                        f"Could not recover process for app '{app_name}': {str(e)}"
                    )
                    self._pid_manager.remove_pid(app_name)
                    self.update_app_status(app_name, False)

    def _get_env_file_path(self, app_name):
        """Get path to env file for an app"""
        return os.path.join(self.storage_path, app_name, ".env")

    def load_app_env(self, app_name):
        """Load environment variables from .env file"""
        env_file = self._get_env_file_path(app_name)
        if os.path.exists(env_file):
            return dotenv_values(env_file)
        return {}

    def save_app_env(self, app_name, env_vars):
        """Save environment variables to .env file"""
        env_file = self._get_env_file_path(app_name)
        app_dir = os.path.dirname(env_file)
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)

        # Clear existing file
        with open(env_file, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        # Update metadata
        for am in self.apps_metadata:
            if am["name"] == app_name:
                am["env"] = env_vars
                self.save_metadata()
                break
