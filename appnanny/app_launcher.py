import os
import socket
import subprocess

import git
import psutil
from dotenv import dotenv_values

from port_utils import find_available_port
from logging_config import logger


class AppLauncher:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def clone_repository(self, app_name, repo):
        """Initial repository clone for new app"""
        app_dir = os.path.join(self.storage_path, app_name)
        if not os.path.exists(app_dir):
            logger.info(f"Creating directory for app '{app_name}': {app_dir}")
            os.makedirs(app_dir)

        try:
            if os.path.exists(os.path.join(app_dir, ".git")):
                logger.error(f"Git repository already exists for app '{app_name}'")
                return None

            logger.info(f"Cloning repository for app '{app_name}' from {repo}")
            git.Repo.clone_from(repo, app_dir)
            return app_dir
        except git.GitCommandError as e:
            logger.error(
                f"Git clone failed for app '{app_name}': {str(e)}", exc_info=True
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error during git clone for app '{app_name}': {str(e)}",
                exc_info=True,
            )
            return None

    def update_repository(self, app_name):
        """Update existing repository"""
        app_dir = os.path.join(self.storage_path, app_name)
        try:
            if not os.path.exists(os.path.join(app_dir, ".git")):
                logger.error(f"No git repository found for app '{app_name}'")
                return False

            logger.info(f"Updating repository for app '{app_name}'")
            git_repo = git.Repo(app_dir)
            git_repo.remotes.origin.pull()
            return True
        except git.GitCommandError as e:
            logger.error(
                f"Git pull failed for app '{app_name}': {str(e)}", exc_info=True
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error during git pull for app '{app_name}': {str(e)}",
                exc_info=True,
            )
            return False

    def launch(self, app_name, app_type, path, env_vars, preferred_port=None):
        """Launch a new application instance"""
        app_dir = os.path.join(self.storage_path, app_name)
        if not os.path.exists(app_dir):
            logger.error(f"App directory not found for '{app_name}'")
            return None

        # Allocate port
        port = self._allocate_port(app_name, preferred_port)
        if not port:
            return None

        # Setup logging
        stdout_log, stderr_log = self._setup_logging(app_dir, app_name)

        # Launch process
        process = self._start_process(
            app_name, app_type, app_dir, path, port, env_vars, stdout_log, stderr_log
        )
        if not process:
            return None

        return port, process

    def _allocate_port(self, app_name, preferred_port=None):
        """Allocate a port for the application"""
        try:
            port = None
            if preferred_port:
                logger.info(
                    f"Checking preferred port {preferred_port} for app '{app_name}'"
                )
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if s.connect_ex(("127.0.0.1", preferred_port)) != 0:
                        port = preferred_port
                        logger.info(f"Using preferred port {port} for app '{app_name}'")
                    else:
                        logger.warning(
                            f"Preferred port {preferred_port} is in use for app '{app_name}'"
                        )

            if not port:
                port = find_available_port()
                if not port:
                    logger.error(f"No available ports found for app '{app_name}'")
                    return None
                logger.info(f"Assigned new port {port} for app '{app_name}'")
            return port
        except Exception as e:
            logger.error(
                f"Port allocation failed for app '{app_name}': {str(e)}", exc_info=True
            )
            return None

    def _setup_logging(self, app_dir, app_name):
        """Setup log files for stdout and stderr"""
        log_dir = os.path.join(app_dir, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        stdout_log = os.path.join(log_dir, f"{app_name}_stdout.log")
        stderr_log = os.path.join(log_dir, f"{app_name}_stderr.log")
        return stdout_log, stderr_log

    def _start_process(
        self, app_name, app_type, app_dir, path, port, env_vars, stdout_log, stderr_log
    ):
        """Start the application process"""
        try:
            # Load .env file if exists
            env = os.environ.copy()
            env_file = os.path.join(app_dir, ".env")
            if os.path.exists(env_file):
                env.update(dotenv_values(env_file))

            # Add runtime variables
            env.update(env_vars)
            env["PORT"] = str(port)

            cmd, workdir = self._build_command(app_type, app_dir, path, port)
            if not cmd:
                logger.error(f"Unsupported app type '{app_type}' for app '{app_name}'")
                return None

            logger.info(f"Launching app '{app_name}' with command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                cwd=workdir,
                env=env,
                stdout=open(stdout_log, "a"),
                stderr=open(stderr_log, "a"),
            )
            # Convert subprocess.Popen to psutil.Process
            psutil_process = psutil.Process(process.pid)
            logger.info(f"App '{app_name}' launched with PID {psutil_process.pid}")
            return psutil_process

        except Exception as e:
            logger.error(
                f"Process launch failed for app '{app_name}': {str(e)}", exc_info=True
            )
            return None

    def _build_command(self, app_type, app_dir, path, port):
        """Build command list based on app type"""
        workdir = os.path.dirname(os.path.join(app_dir, path))
        scriptfile = os.path.basename(path)
        if app_type == "streamlit":
            cmd = ["streamlit", "run", scriptfile, "--server.port", str(port)]
        elif app_type == "voila":
            cmd = ["voila", scriptfile, "--port", str(port)]
        elif app_type == "flask":
            cmd = ["python", scriptfile, "--port", str(port)]
        else:
            cmd = []
        return cmd, workdir
