import os
import time
import requests
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watcher.config import load_config

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, cfg):
        self.cfg = cfg

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(self.cfg["WATCH_EXTENSIONS"]):
            return
        if any(ignored in event.src_path for ignored in self.cfg["IGNORE_DIRS"]):
            return

        print(f"📄 Changed: {event.src_path}")
        try:
            with open(event.src_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i in range(0, len(lines), self.cfg["CHUNK_SIZE"]):
                text = "".join(lines[i:i+self.cfg["CHUNK_SIZE"]]).strip()
                if text:
                    metadata = {
                        "project": self.cfg["PROJECT_NAME"],
                        "file": os.path.relpath(event.src_path, self.cfg["WATCH_DIR"]),
                        "line": i + 1
                    }
                    requests.post(
                        self.cfg["EMBED_SERVER_URL"],
                        json={"text": text, "metadata": metadata}
                    )
        except Exception as e:
            print(f"❌ Failed to read/send file: {e}")


def start():
    try:
        cfg = load_config()
    except RuntimeError as err:
        print(f"❌ Config error: {err}")
        return

    observer = Observer()
    observer.schedule(CodeChangeHandler(cfg), path=cfg["WATCH_DIR"], recursive=True)
    observer.start()
    print(f"👀 Watching: {cfg['WATCH_DIR']}")

    try:
        while True:
            # Debounce to avoid rapid-fire requests
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start()
