from __future__ import annotations

import atexit
import logging
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional

import docker
import httpx
from docker.errors import APIError, DockerException, NotFound
from docker.models.containers import Container


@dataclass
class DockerService:
    image: str = "jyxsu6/medagentbench:latest"
    container_name: str = "medagentbench_mcp_managed"
    host_port: int = 8080
    container_port: int = 8080
    ready_timeout_s: int = 180
    pull: bool = True
    stream_logs: bool = False

    _client: Optional[docker.DockerClient] = None
    _container: Optional[Container] = None
    _stop_event: threading.Event = threading.Event()
    _log_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._client = self._get_docker_client()

        if self.pull:
            print(f"Pulling image {self.image} ...")
            self._client.images.pull(self.image)

        try:
            old = self._client.containers.get(self.container_name)
            print(f"Removing existing container {self.container_name} ...")
            try:
                old.remove(force=True)
            except Exception as e:
                print(f"Failed to remove old container: {e}")
        except NotFound:
            print("No existing container found.")
            old = None

        print(
            f"Starting container {self.image} (port {self.host_port} -> {self.container_port}) ..."
        )

        try:
            self._container = self._client.containers.run(
                self.image,
                name=self.container_name,
                detach=True,
                ports={f"{self.container_port}/tcp": self.host_port},
                remove=False,
            )
        except APIError as e:
            if "port is already allocated" in str(e).lower():
                raise RuntimeError(
                    f"Port {self.host_port} is already in use. "
                    "Stop the process using it or change host_port."
                ) from e
            raise

        if self.stream_logs:
            self._start_log_stream()

        self._wait_until_ready()

        print(f"Container ready. Base URL: http://127.0.0.1:{self.host_port}")

    def stop(self) -> None:
        self._stop_event.set()

        if self._log_thread and self._log_thread.is_alive():
            print("Stopping log stream ...", flush=True)
            self._log_thread.join()

        if not self._client:
            print("Docker client not initialized; nothing to stop.", flush=True)
            return

        if not self._container:
            try:
                self._container = self._client.containers.get(self.container_name)
            except NotFound:
                print("Container not found; nothing to stop.", flush=True)
                return

        try:
            print(f"Stopping container {self.container_name} ...", flush=True)
            self._container.stop(timeout=10)
            try:
                print(f"Removing container {self.container_name} ...", flush=True)
                self._container.remove(force=True)
            except Exception as e:
                print(f"Error removing container: {e}", flush=True)
        except Exception as e:
            print(f"Error stopping container: {e}", flush=True)

    def _get_docker_client(self) -> docker.DockerClient:
        try:
            client = docker.from_env()
            client.ping()
            return client
        except DockerException as e:
            raise RuntimeError("Docker is not running or not accessible.") from e

    def _start_log_stream(self) -> None:
        if self._container is None:
            raise RuntimeError("Cannot stream logs: container is not running.")
        self._stop_event.clear()

        def _stream():
            try:
                for line in self._container.logs(stream=True, follow=True):
                    if self._stop_event.is_set():
                        break
                    text = line.decode("utf-8", errors="replace").rstrip()
                    if text:
                        print(f"[container] {text}")
            except Exception as e:
                print(f"Log stream ended: {e}")

        self._log_thread = threading.Thread(
            target=_stream, name="container-logs", daemon=True
        )
        self._log_thread.start()

    def _wait_until_ready(self) -> None:
        deadline = time.time() + self.ready_timeout_s
        host = "127.0.0.1"
        port = self.host_port

        url = f"http://{host}:{port}/"
        with httpx.Client(timeout=2.0) as client:
            while time.time() < deadline:
                if self._stop_event.is_set():
                    raise RuntimeError("Stopped while waiting for container readiness.")
                try:
                    r = client.get(url)
                    print("HTTP ready check: %s -> %s", url, r.status_code)
                    return
                except Exception:
                    time.sleep(2)

        raise TimeoutError(f"Timed out waiting for HTTP server at {url}.")


_shutdown_once = threading.Event()


def start_service() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    service = DockerService(image="jyxsu6/medagentbench:latest")

    def shutdown(reason: str) -> None:
        if _shutdown_once.is_set():
            return
        _shutdown_once.set()
        if not sys.stdout.closed:
            print(f"Shutting down ({reason}) ...", flush=True)
        # with suppress(Exception):
        service.stop()

    atexit.register(shutdown, "atexit")

    def _handle_signal(signum, frame):
        shutdown(f"signal {signum}")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    service.start()
