from __future__ import annotations

import atexit
import signal
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
    container_name: str = "medagentbench"
    host_port: int = 8080
    container_port: int = 8080
    ready_timeout_s: int = 180

    _client: Optional[docker.DockerClient] = None
    _container: Optional[Container] = None
    _stop_event: threading.Event = threading.Event()

    def start(self) -> None:
        self._client = self._get_docker_client()

        try:
            self._client.images.get(self.image)
            print(f"Image {self.image} found locally.")
        except NotFound:
            print(f"Image {self.image} not found locally. Pulling from Docker Hub ...")
            try:
                self._client.images.pull(self.image)
                print(f"Successfully pulled image {self.image}.")
            except APIError as e:
                raise RuntimeError(f"Failed to pull image {self.image}: {e}") from e

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

        self._wait_until_ready()

        print(f"Container ready. Base URL: http://127.0.0.1:{self.host_port}")

    def stop(self) -> None:
        self._stop_event.set()

        if not self._client:
            print("Docker client not initialized; nothing to stop.")
            return

        if not self._container:
            try:
                self._container = self._client.containers.get(self.container_name)
            except NotFound:
                print("Container not found; nothing to stop.")
                return

        try:
            print(f"Stopping container {self.container_name} ...")
            self._container.stop()
            try:
                print(f"Removing container {self.container_name} ...")
                self._container.remove(force=True)
            except Exception as e:
                print(f"Error removing container: {e}")
        except Exception as e:
            print(f"Error stopping container: {e}")

    def _get_docker_client(self) -> docker.DockerClient:
        try:
            client = docker.from_env()
            client.ping()
            return client
        except DockerException as e:
            raise RuntimeError("Docker is not running or not accessible.") from e

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
                    response = client.get(url)
                    print(f"HTTP ready check: {url} -> {response.status_code}")
                    return
                except Exception:
                    time.sleep(2)

        raise TimeoutError(f"Timed out waiting for HTTP server at {url}.")


_shutdown_once = threading.Event()


def start_service() -> None:
    service = DockerService(image="jyxsu6/medagentbench:latest")

    def shutdown(reason: str) -> None:
        if _shutdown_once.is_set():
            return
        _shutdown_once.set()
        print(f"Shutting down ({reason}) ...")
        service.stop()

    atexit.register(shutdown, "atexit")

    def _handle_signal(signum, frame):
        shutdown(f"signal {signum}")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    service.start()
