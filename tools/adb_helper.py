import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import subprocess
from tools.logger import get_logger

log = get_logger()

def run_adb_command(cmd):
    try:
        result = subprocess.run(["adb"] + cmd.split(), capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log.error(f"ADB command failed: {e.stderr.strip()}")
        return None

def install_apk(apk_path):
    log.info(f"Installing {apk_path}...")
    return run_adb_command(f"install -r {apk_path}")

def launch_app(package_name):
    log.info(f"Launching {package_name}...")
    return run_adb_command(f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1")

def logcat(filter="*:*"):
    log.info("Starting logcat...")
    subprocess.run(["adb", "logcat", filter])
