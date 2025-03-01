import logging
from logging.handlers import RotatingFileHandler
import time

import requests
from apscheduler.schedulers.background import BackgroundScheduler


# Configure logging
LOG_FILE = "scheduler.log"
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("appnanny_scheduler")
handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=2)
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)

API_BASE = "http://localhost:5000"
EXPIRY_TIME = 3 * 24 * 3600  # 3 days in seconds


def check_expired_apps():
    """Check and stop expired apps via API calls"""
    logger.info("Running check_expired_apps...")
    try:
        # Get list of all apps
        response = requests.get(f"{API_BASE}/apps")
        if response.status_code != 200:
            logger.error(f"Failed to get apps list: {response.text}")
            return

        apps = response.json()
        current_time = time.time()

        for app_name, info in apps.items():
            if info["running"]:
                uptime = current_time - info.get("last_access_time", info["uptime"])
                if uptime > EXPIRY_TIME:
                    logger.info(
                        f"Stopping expired app {app_name} (idle for {uptime/3600:.1f} hours)"
                    )
                    stop_response = requests.post(f"{API_BASE}/stop/{app_name}")
                    if stop_response.status_code != 200:
                        logger.error(
                            f"Failed to stop app {app_name}: {stop_response.text}"
                        )

    except Exception as e:
        logger.exception("Error in check_expired_apps")


def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_expired_apps, "interval", minutes=5)
    scheduler.start()

    try:
        # Keep the script running
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
