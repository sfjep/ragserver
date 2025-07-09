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

        relative_path = os.path.relpath(event.src_path, self.cfg["WATCH_DIR"])
        print(f"📄 Changed: {relative_path}")

        try:
            self.delete_existing_embeddings(relative_path)
            self.upload_chunks(event.src_path, relative_path)
        except Exception as e:
            print(f"❌ Error processing {relative_path}: {e}")


    def delete_existing_embeddings(self, relative_path: str):
        try:
            res = requests.delete(
                self.cfg["EMBED_SERVER_URL"],
                params={"file": relative_path}
            )
            if res.status_code != 200:
                print(f"⚠️ Failed to delete embeddings: {res.text}")
            else:
                print(f"✅ Deleted existing embeddings for {relative_path}")
        except Exception as e:
            print(f"❌ DELETE failed for {relative_path}: {e}")

    def upload_chunks(self, full_path: str, relative_path: str):
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i in range(0, len(lines), self.cfg["CHUNK_SIZE"]):
            chunk = "".join(lines[i:i + self.cfg["CHUNK_SIZE"]]).strip()
            if not chunk:
                continue

            metadata = {
                "project": self.cfg["PROJECT_NAME"],
                "file": relative_path,
                "line": i + 1
            }

            try:
                res = requests.post(
                    self.cfg["EMBED_SERVER_URL"],
                    json={"text": chunk, "metadata": metadata}
                )
                if res.status_code != 200:
                    print(f"⚠️ Failed to embed chunk {relative_path}:{i + 1}")
            except Exception as e:
                print(f"❌ POST failed for chunk {relative_path}:{i + 1}: {e}")


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
