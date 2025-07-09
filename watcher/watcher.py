import os
import time
import requests
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

load_dotenv()

# Load YAML config
with open("ragconfig.yml", "r") as f:
    config = yaml.safe_load(f)

WATCH_DIR = os.environ["WATCH_DIR"]
EMBED_SERVER_URL = "http://server:8000/embed"
WATCH_EXTENSIONS = tuple(config.get("watch_extensions", []))
IGNORE_DIRS = set(config.get("ignore_dirs", []))
CHUNK_SIZE = config.get("chunk_size", 20)
PROJECT_NAME = os.environ.get("PROJECT_NAME", "default")

class CodeChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(WATCH_EXTENSIONS):
            return

        if any(ignored in event.src_path for ignored in IGNORE_DIRS):
            return

        print(f"📄 Changed: {event.src_path}")
        try:
            with open(event.src_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i in range(0, len(lines), CHUNK_SIZE):
                text = "".join(lines[i:i+CHUNK_SIZE]).strip()
                if text:
                    metadata = {
                        "project": PROJECT_NAME,
                        "file": os.path.relpath(event.src_path, WATCH_DIR),
                        "line": i+1
                    }
                    requests.post(EMBED_SERVER_URL, json={"text": text, "metadata": metadata})
        except Exception as e:
            print(f"❌ Failed to read/send file: {e}")
