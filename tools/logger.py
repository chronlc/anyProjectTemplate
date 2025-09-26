import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sys

class Logger:
    COLORS = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARN": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m",
    }

    def _log(self, level, msg):
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"]
        sys.stdout.write(f"{color}[{level}] {msg}{reset}\n")

    def info(self, msg): self._log("INFO", msg)
    def success(self, msg): self._log("SUCCESS", msg)
    def warn(self, msg): self._log("WARN", msg)
    def error(self, msg): self._log("ERROR", msg)

def get_logger():
    return Logger()
