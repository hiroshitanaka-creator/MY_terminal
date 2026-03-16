import os

PORT = int(os.environ.get("PORT", 8765))
SECRET_TOKEN = os.environ.get("MY_TERMINAL_TOKEN", "changeme")
SHELL = os.environ.get("SHELL", "/bin/bash")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PRESETS_FILE = os.path.join(DATA_DIR, "api_presets.json")
