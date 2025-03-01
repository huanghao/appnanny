import os
import socket
import subprocess
from logging_config import logger
from port_utils import find_available_port
import git
import psutil


class AppLauncher:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def launch(self, app_name, app_type, repo, path, env_vars, preferred_port=None):
        """Launch a new application instance"""
        logger.info(
            f"Starting launch process for app '{app_name}' (type: {app_type}, repo: {repo})"
        )

        # Setup app directory and repo
        app_dir = self._setup_app_directory(app_name, repo)
        if not app_dir:
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

    def _setup_app_directory(self, app_name, repo):
        """Setup application directory and clone/update repository"""
        app_dir = os.path.join(self.storage_path, app_name)
        if not os.path.exists(app_dir):
            logger.info(f"Creating directory for app '{app_name}': {app_dir}")
            os.makedirs(app_dir)

        try:
            if not os.path.exists(os.path.join(app_dir, ".git")):
                logger.info(f"Cloning repository for app '{app_name}' from {repo}")
                git.Repo.clone_from(repo, app_dir)
            else:
                logger.info(f"Updating existing repository for app '{app_name}'")
                git_repo = git.Repo(app_dir)
                git_repo.remotes.origin.pull()
            return app_dir
        except git.GitCommandError as e:
            logger.error(
                f"Git operation failed for app '{app_name}': {str(e)}", exc_info=True
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error during git operation for app '{app_name}': {str(e)}",
                exc_info=True,
            )
            return None

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
            cmd = self._build_command(app_type, path, port)
            if not cmd:
                logger.error(f"Unsupported app type '{app_type}' for app '{app_name}'")
                return None

            env = os.environ.copy()
            env.update(env_vars)
            env["PORT"] = str(port)

            logger.info(f"Launching app '{app_name}' with command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                cwd=app_dir,
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

    def _build_command(self, app_type, path, port):
        """Build command list based on app type"""
        if app_type == "streamlit":
            return ["streamlit", "run", path, "--server.port", str(port)]
        elif app_type == "voila":
            return ["voila", path, "--port", str(port)]
        elif app_type == "flask":
            return ["python", path, "--port", str(port)]
        return None
