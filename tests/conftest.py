from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import time
import threading
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import httpx
import uvicorn

SERVER_SRC = Path(__file__).resolve().parents[1].parent / "personal-server" / "src"
SERVER_SRC = SERVER_SRC.resolve()
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from personal_server.core.config import Settings
from personal_server.main import create_app


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def mongod_uri() -> Iterator[str]:
    port = _find_free_port()
    temp_dir = tempfile.TemporaryDirectory(prefix="personal-cli-mongo-")
    process = subprocess.Popen(
        [
            "mongod",
            "--dbpath",
            temp_dir.name,
            "--bind_ip",
            "127.0.0.1",
            "--port",
            str(port),
            "--nounixsocket",
            "--quiet",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    uri = f"mongodb://127.0.0.1:{port}"
    client = MongoClient(uri, serverSelectionTimeoutMS=200)
    try:
        deadline = time.time() + 20
        while True:
            try:
                client.admin.command("ping")
                break
            except Exception:
                if time.time() >= deadline:
                    raise RuntimeError(f"Timed out waiting for mongod at {uri}")
                time.sleep(0.2)
        yield uri
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        temp_dir.cleanup()


@pytest.fixture()
def mongo_db_name() -> str:
    return f"personal_cli_test_{uuid4().hex}"


@pytest.fixture()
def app_settings(mongod_uri: str, mongo_db_name: str) -> Settings:
    return Settings(mongo_uri=mongod_uri, mongo_db_name=mongo_db_name, personal_api_key="")


@pytest.fixture()
def app(app_settings: Settings):
    app = create_app(app_settings)
    mongo_client = AsyncIOMotorClient(app_settings.mongo_uri)
    app.state.mongo_client = mongo_client
    app.state.db = mongo_client[app_settings.mongo_db_name]
    try:
        yield app
    finally:
        mongo_client.close()


@pytest.fixture()
def live_server(app) -> Iterator[str]:
    port = _find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="on")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 20
    try:
        while True:
            try:
                response = httpx.get(f"{base_url}/healthz", timeout=0.5)
                if response.status_code == 200:
                    break
            except Exception:
                pass
            if time.time() >= deadline:
                raise RuntimeError(f"Timed out waiting for server at {base_url}")
            time.sleep(0.2)
        yield base_url
    finally:
        server.should_exit = True
        thread.join(timeout=10)
