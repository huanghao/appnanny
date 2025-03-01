from flask import Blueprint, request, jsonify

from logging_config import logger

app_controller = Blueprint("app_controller", __name__)
_app_service = None


def init_controller(app_service):
    """Initialize controller with app service instance"""
    global _app_service
    _app_service = app_service


@app_controller.route("/create", methods=["POST"])
def create_app():
    """Handle app creation requests"""
    try:
        data = request.json
        port = _app_service.create_app(
            data["name"],
            data["type"],
            data["repo"],
            data["path"],
            data["email"],
            data.get("env", {}),
        )

        if port:
            logger.info(f"Created and started app '{data['name']}' on port {port}.")
            return jsonify({"message": f"App '{data['name']}' started", "port": port})
        else:
            logger.error("Failed to create app. No port or command.")
            return jsonify({"error": "No available port or invalid type"}), 400

    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error creating app: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app_controller.route("/stop/<app_name>", methods=["POST"])
def stop_app(app_name):
    """Handle app stop requests"""
    if _app_service.stop_app(app_name):
        return jsonify({"message": f"App '{app_name}' stopped"})
    return jsonify({"error": f"Failed to stop app '{app_name}'"}, 400)


@app_controller.route("/restart/<app_name>", methods=["POST"])
def restart_app(app_name):
    """Handle app restart requests"""
    port = _app_service.restart_app(app_name)
    if port:
        return jsonify(
            {"message": f"App '{app_name}' restarted on port {port}", "port": port}
        )
    return jsonify({"error": f"Failed to restart app '{app_name}'"}, 400)


@app_controller.route("/heartbeat/<app_name>", methods=["POST"])
def update_access_time(app_name):
    """Handle app heartbeat requests"""
    if _app_service.update_access_time(app_name):
        return jsonify({"status": "ok"})
    return jsonify({"error": "App not found"}), 404


@app_controller.route("/apps", methods=["GET"])
def list_apps():
    """Handle app listing requests"""
    try:
        apps = _app_service.list_apps()
        return jsonify(apps)
    except Exception as e:
        logger.error(f"Error listing apps: {str(e)}")
        return jsonify({"error": "Failed to list apps"}), 500


@app_controller.route("/start/<app_name>", methods=["POST"])
def start_app(app_name):
    """Handle app start requests"""
    port = _app_service.start_app(app_name)
    if port:
        return jsonify(
            {"message": f"App '{app_name}' started on port {port}", "port": port}
        )
    return jsonify({"error": "Failed to start app"}), 400
