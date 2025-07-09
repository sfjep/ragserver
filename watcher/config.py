import os
import yaml
from dotenv import load_dotenv

load_dotenv()

def load_config():
    """Load environment variables and YAML config for the watcher."""
    config_path = "ragconfig.yml"
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return {
        "WATCH_DIR": os.environ["WATCH_DIR"],
        "PROJECT_NAME": os.environ.get("PROJECT_NAME", "default"),
        "EMBED_SERVER_URL": os.environ.get("EMBED_SERVER_URL", "http://server:8000/embed"),
        "WATCH_EXTENSIONS": tuple(config.get("watch_extensions", [])),
        "IGNORE_DIRS": set(config.get("ignore_dirs", [])),
        "CHUNK_SIZE": config.get("chunk_size", 20),
    }
