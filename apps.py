#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AppNanny: A single-file demonstration of a service that manages multiple apps (Streamlit, Voila, etc.),
with:
- Flask-based REST API for creation/stop/restart.
- File-based metadata storage (so that if the service restarts, we can recover the info).
- Streamlit-based UI in the same file (run via `streamlit run appnanny.py`).
- Incorporates some ideas from more robust designs: logging, APScheduler for periodic tasks, GitPython for repo management, etc.
"""

import os
import json
import subprocess
import time
import signal
import socket
import threading
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, jsonify


# Additional third-party libs
from apscheduler.schedulers.background import BackgroundScheduler
import git

# ========================================================================
# Logging configuration
# ========================================================================
LOG_FILE = "appnanny.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("appnanny")

# rotating file handler
handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=2)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# ========================================================================
# Configuration
# ========================================================================
PORT_RANGE = list(range(8080, 8090)) + list(range(4040, 4050))  # narrower for demo
APP_STORAGE_PATH = "./apps"
APP_METADATA_FILE = os.path.join(APP_STORAGE_PATH, "apps_metadata.json")
if not os.path.exists(APP_STORAGE_PATH):
    os.makedirs(APP_STORAGE_PATH)

CHECK_INTERVAL = 3600  # seconds between checks for expiration
EXPIRY_TIME = 3 * 24 * 3600  # 3 days in seconds
DELETE_WARNING_TIME = 30 * 24 * 3600  # 7 days in seconds (not fully implemented in demo)
EMAIL_SENDER = "noreply@appnanny.com"
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USER = "your_smtp_user"
SMTP_PASS = "your_smtp_password"

# ========================================================================
# Flask app for RESTful management
# ========================================================================
app = Flask(__name__)

# in-memory structure for running processes: {app_name: {pid, port, start_time, process}}
running_apps = {}
# persistent metadata for all apps, whether running or not
# each entry: {
#   "name": app_name,
#   "type": app_type,
#   "repo": repo,
#   "path": path,
#   "email": email,
#   "env": {k:v},
#   "last_start_time": float,
#   "is_active": bool
# }
apps_metadata = []

# ========================================================================
# Utility: load/store metadata
# ========================================================================

def load_metadata():
    global apps_metadata
    if os.path.exists(APP_METADATA_FILE):
        with open(APP_METADATA_FILE, "r") as f:
            apps_metadata = json.load(f)
    else:
        apps_metadata = []


def save_metadata():
    global apps_metadata
    with open(APP_METADATA_FILE, "w") as f:
        json.dump(apps_metadata, f, indent=2)

# ========================================================================
# find available port
# ========================================================================

def find_available_port():
    for port in PORT_RANGE:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return None

# ========================================================================
# launch app (in separate process) with improvements from example:
# - Logging to files
# - GitPython for repo ops
# ========================================================================

def launch_app(app_name, app_type, repo, path, env_vars):
    """Clones/pulls code if needed, then starts a subprocess with logs."""
    logger.info(f"Launching app '{app_name}' of type '{app_type}' from repo '{repo}'")
    app_dir = os.path.join(APP_STORAGE_PATH, app_name)
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)

    # pick port
    port = find_available_port()
    if not port:
        logger.error("No available port found!")
        return None

    # store env
    env_path = os.path.join(app_dir, "env.json")
    with open(env_path, "w") as f:
        json.dump(env_vars, f)

    # clone or pull using GitPython
    src_dir = os.path.join(app_dir, "src")
    if not os.path.exists(src_dir):
        # clone fresh
        try:
            logger.info(f"Cloning repo {repo} into {src_dir}.")
            git.Repo.clone_from(repo, src_dir)
        except Exception as e:
            logger.error(f"Failed to clone repo: {e}")
            return None
    else:
        # pull updates
        try:
            logger.info(f"Pulling latest from {repo} in {src_dir}.")
            g = git.Repo(src_dir)
            g.remotes.origin.pull()
        except Exception as e:
            logger.error(f"Failed to pull repo updates: {e}")
            return None

    # build the command
    command_map = {
        "streamlit": f"streamlit run {path} --server.port={port}",
        "voila": f"voila {path} --port={port}",
        "gradio": f"python {path}",
        "flask": f"python -m flask run --port={port}",
        "fastapi": f"uvicorn {path} --host 0.0.0.0 --port={port}"
    }
    command = command_map.get(app_type)

    if not command:
        logger.error(f"Unsupported app_type '{app_type}'.")
        return None

    full_env = dict(os.environ)
    for k, v in env_vars.items():
        # ensure everything is string
        full_env[k] = str(v)

    logs_dir = os.path.join(app_dir, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    stdout_log = open(os.path.join(logs_dir, "stdout.log"), 'ab')
    stderr_log = open(os.path.join(logs_dir, "stderr.log"), 'ab')

    process = subprocess.Popen(
        command,
        shell=True,
        cwd=src_dir,
        env=full_env,
        stdout=stdout_log,
        stderr=stderr_log
    )

    running_apps[app_name] = {
        "pid": process.pid,
        "port": port,
        "start_time": time.time(),
        "process": process
    }

    logger.info(f"Launched app '{app_name}' on port {port} (PID={process.pid}).")
    return port

# ========================================================================
# stop app
# ========================================================================

def stop_app(app_name):
    """Stop the process, mark it inactive"""
    if app_name in running_apps:
        pid = running_apps[app_name]["pid"]
        logger.info(f"Stopping app '{app_name}' with PID={pid}.")
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        del running_apps[app_name]

    # mark is_active=False in metadata
    for am in apps_metadata:
        if am["name"] == app_name:
            am["is_active"] = False
    save_metadata()

# ========================================================================
# restart app
# ========================================================================
def restart_app(app_name):
    # first read from metadata
    md = None
    for am in apps_metadata:
        if am["name"] == app_name:
            md = am
            break
    if not md:
        logger.warning(f"Cannot restart. Metadata for '{app_name}' not found.")
        return

    stop_app(app_name)

    new_port = launch_app(
        app_name,
        md["type"],
        md["repo"],
        md["path"],
        md["env"]
    )
    if new_port:
        md["is_active"] = True
        md["last_start_time"] = time.time()
        save_metadata()

# ========================================================================
# check expired apps (APS) with interval
# ========================================================================

def check_expired_apps():
    logger.info("Running check_expired_apps...")
    current_time = time.time()
    to_stop = []
    for app_name, data in list(running_apps.items()):
        # for demo, only do a simple check: if (now - start_time) > EXPIRY_TIME, stop.
        if (current_time - data["start_time"]) > EXPIRY_TIME:
            to_stop.append(app_name)
    for appn in to_stop:
        logger.info(f"App '{appn}' exceeded expiry, stopping.")
        stop_app(appn)

# ========================================================================
# Flask endpoints
# ========================================================================
@app.route("/create", methods=["POST"])
def create_app():
    data = request.json
    app_name = data["name"]
    app_type = data["type"]
    repo = data["repo"]
    path = data["path"]
    email = data["email"]
    env_vars = data.get("env", {})

    # ensure metadata stored
    found = False
    for am in apps_metadata:
        if am["name"] == app_name:
            found = True
            am["type"] = app_type
            am["repo"] = repo
            am["path"] = path
            am["email"] = email
            am["env"] = env_vars
            break
    if not found:
        apps_metadata.append({
            "name": app_name,
            "type": app_type,
            "repo": repo,
            "path": path,
            "email": email,
            "env": env_vars,
            "last_start_time": 0,
            "is_active": False
        })

    save_metadata()

    port = launch_app(app_name, app_type, repo, path, env_vars)
    if port:
        for am in apps_metadata:
            if am["name"] == app_name:
                am["is_active"] = True
                am["last_start_time"] = time.time()
        save_metadata()
        logger.info(f"Created and started app '{app_name}' on port {port}.")
        return jsonify({"message": f"App '{app_name}' started", "port": port})
    else:
        logger.error("Failed to create app. No port or command.")
        return jsonify({"error": "No available port or invalid type"}), 400

@app.route("/stop/<app_name>", methods=["POST"])
def stop_endpoint(app_name):
    stop_app(app_name)
    return jsonify({"message": f"App '{app_name}' stopped"})

@app.route("/restart/<app_name>", methods=["POST"])
def restart_endpoint(app_name):
    restart_app(app_name)
    return jsonify({"message": f"App '{app_name}' restarted"})

@app.route("/apps", methods=["GET"])
def list_apps():
    all_info = {}
    for am in apps_metadata:
        name = am["name"]
        is_running = (name in running_apps)
        port = running_apps[name]["port"] if is_running else None
        start_time = running_apps[name]["start_time"] if is_running else 0
        all_info[name] = {
            "type": am["type"],
            "repo": am["repo"],
            "path": am["path"],
            "email": am["email"],
            "env": am["env"],
            "is_active": am["is_active"],
            "running": is_running,
            "port": port,
            "uptime": time.time() - start_time if is_running else 0
        }
    return jsonify(all_info)

# ========================================================================
# On startup, load metadata.
# For demonstration, do not attempt to re-attach to running pids.
# (We could do so by scanning for processes, etc.)
# ========================================================================
load_metadata()

# set up APScheduler to handle periodic tasks
scheduler = BackgroundScheduler()
scheduler.add_job(check_expired_apps, 'interval', minutes=5)
scheduler.start()


# 只在作为主模块运行时启动Flask服务器
if __name__ == "__main__":
    logger.info("Starting Flask server on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)

