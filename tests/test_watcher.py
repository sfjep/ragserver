import os
import tempfile
import shutil
import types
import pytest
import builtins
from unittest import mock
import yaml

import watcher.watcher as watcher

@pytest.fixture
def temp_watch_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

@pytest.fixture
def temp_config_file(tmp_path):
    config = {
        "watch_extensions": [".py", ".txt"],
        "ignore_dirs": ["__pycache__"],
        "chunk_size": 2
    }
    config_path = tmp_path / "ragconfig.yml"
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)
    return str(config_path)

def test_load_config_success(monkeypatch, temp_watch_dir, temp_config_file):
    monkeypatch.setenv("WATCH_DIR", temp_watch_dir)
    monkeypatch.setenv("PROJECT_NAME", "proj1")
    monkeypatch.setattr(watcher, "load_dotenv", lambda: None)
    monkeypatch.setattr(builtins, "open", mock.mock_open(read_data="""
watch_extensions:
  - .py
  - .txt
ignore_dirs:
  - __pycache__
chunk_size: 2
"""))
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    cfg = watcher.load_config()
    assert cfg["WATCH_DIR"] == temp_watch_dir
    assert cfg["PROJECT_NAME"] == "proj1"
    assert cfg["EMBED_SERVER_URL"] == "http://server:8000/embed"
    assert ".py" in cfg["WATCH_EXTENSIONS"]
    assert "__pycache__" in cfg["IGNORE_DIRS"]
    assert cfg["CHUNK_SIZE"] == 2

def test_load_config_missing_watch_dir(monkeypatch):
    monkeypatch.setenv("WATCH_DIR", "")
    monkeypatch.setattr(watcher, "load_dotenv", lambda: None)
    monkeypatch.setattr(builtins, "open", mock.mock_open(read_data="watch_extensions: []"))
    with pytest.raises(RuntimeError, match="WATCH_DIR is not set"):
        watcher.load_config()

def test_load_config_watch_dir_not_exists(monkeypatch):
    monkeypatch.setenv("WATCH_DIR", "/not/exist")
    monkeypatch.setattr(watcher, "load_dotenv", lambda: None)
    monkeypatch.setattr(builtins, "open", mock.mock_open(read_data="watch_extensions: []"))
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    with pytest.raises(RuntimeError, match="does not exist"):
        watcher.load_config()

def test_load_config_bad_yaml(monkeypatch):
    monkeypatch.setenv("WATCH_DIR", "/tmp")
    monkeypatch.setattr(watcher, "load_dotenv", lambda: None)
    monkeypatch.setattr(builtins, "open", mock.mock_open(read_data=":bad_yaml:"))
    monkeypatch.setattr(os.path, "exists", lambda p: True)
    with pytest.raises(RuntimeError, match="Could not load ragconfig.yml"):
        watcher.load_config()

def test_code_change_handler_on_modified_ignored(monkeypatch, tmp_path):
    cfg = {
        "WATCH_EXTENSIONS": (".py",),
        "IGNORE_DIRS": {"__pycache__"},
        "CHUNK_SIZE": 2,
        "PROJECT_NAME": "proj",
        "WATCH_DIR": str(tmp_path),
        "EMBED_SERVER_URL": "http://server:8000/embed"
    }
    handler = watcher.CodeChangeHandler(cfg)
    event = types.SimpleNamespace(
        is_directory=False,
        src_path=str(tmp_path / "__pycache__/foo.py")
    )
    with mock.patch("builtins.open") as m:
        handler.on_modified(event)
        m.assert_not_called()

def test_code_change_handler_on_modified_not_matching_ext(tmp_path):
    cfg = {
        "WATCH_EXTENSIONS": (".py",),
        "IGNORE_DIRS": set(),
        "CHUNK_SIZE": 2,
        "PROJECT_NAME": "proj",
        "WATCH_DIR": str(tmp_path),
        "EMBED_SERVER_URL": "http://server:8000/embed"
    }
    handler = watcher.CodeChangeHandler(cfg)
    event = types.SimpleNamespace(
        is_directory=False,
        src_path=str(tmp_path / "foo.txt")
    )
    with mock.patch("builtins.open") as m:
        handler.on_modified(event)
        m.assert_not_called()

def test_code_change_handler_on_modified_success(tmp_path, monkeypatch):
    test_file = tmp_path / "foo.py"
    test_file.write_text("line1\nline2\nline3\n")
    cfg = {
        "WATCH_EXTENSIONS": (".py",),
        "IGNORE_DIRS": set(),
        "CHUNK_SIZE": 2,
        "PROJECT_NAME": "proj",
        "WATCH_DIR": str(tmp_path),
        "EMBED_SERVER_URL": "http://server:8000/embed"
    }
    handler = watcher.CodeChangeHandler(cfg)
    event = types.SimpleNamespace(
        is_directory=False,
        src_path=str(test_file)
    )
    posts = []
    monkeypatch.setattr(watcher.requests, "post", lambda url, json: posts.append((url, json)))
    handler.on_modified(event)
    assert len(posts) == 2
    assert posts[0][1]["text"] == "line1\nline2"
    assert posts[0][1]["metadata"]["file"] == "foo.py"
    assert posts[0][1]["metadata"]["line"] == 1
    assert posts[1][1]["text"] == "line3"
    assert posts[1][1]["metadata"]["line"] == 3

def test_code_change_handler_on_modified_file_error(tmp_path, capsys):
    cfg = {
        "WATCH_EXTENSIONS": (".py",),
        "IGNORE_DIRS": set(),
        "CHUNK_SIZE": 2,
        "PROJECT_NAME": "proj",
        "WATCH_DIR": str(tmp_path),
        "EMBED_SERVER_URL": "http://server:8000/embed"
    }
    handler = watcher.CodeChangeHandler(cfg)
    event = types.SimpleNamespace(
        is_directory=False,
        src_path=str(tmp_path / "nofile.py")
    )
    handler.on_modified(event)
    captured = capsys.readouterr()
    assert "❌ Failed to read/send file" in captured.out