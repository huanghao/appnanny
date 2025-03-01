import os
from logging_config import logger


class PIDManager:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def save_pid(self, app_name, pid):
        """Save process ID to file"""
        pid_file = self._get_pid_file_path(app_name)
        try:
            logger.debug(f"Saving PID {pid} for app '{app_name}'")
            with open(pid_file, "w") as f:
                f.write(str(pid))
        except Exception as e:
            logger.error(
                f"Failed to save PID file for app '{app_name}': {str(e)}", exc_info=True
            )

    def get_pid(self, app_name):
        """Get process ID from file"""
        pid_file = self._get_pid_file_path(app_name)
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    return int(f.read().strip())
            except Exception as e:
                logger.error(f"Failed to read PID file for {app_name}: {str(e)}")
        return None

    def remove_pid(self, app_name):
        """Remove PID file"""
        pid_file = self._get_pid_file_path(app_name)
        if os.path.exists(pid_file):
            try:
                logger.debug(f"Removing PID file for app '{app_name}'")
                os.remove(pid_file)
            except Exception as e:
                logger.error(
                    f"Failed to remove PID file for app '{app_name}': {str(e)}",
                    exc_info=True,
                )

    def is_process_running(self, pid):
        """Check if a process is running by PID"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _get_pid_file_path(self, app_name):
        """Get the path to PID file for an app"""
        return os.path.join(self.storage_path, app_name, "app.pid")
