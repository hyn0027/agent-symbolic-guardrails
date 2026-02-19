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

from config_loader import CONFIG

DOCKER_CONFIG = CONFIG.DATASET.DOCKER


@dataclass
class DockerService:
    image: str
    container_name: str
    host_port: int
    container_port: int
    ready_timeout_s: int
    restart_if_running: bool = False
    reuse_stopped_container: bool = False

    _client: Optional[docker.DockerClient] = None
    _container: Optional[Container] = None
    _stop_event: threading.Event = threading.Event()

    def start(
        self,
    ) -> None:
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
            container = self._client.containers.get(self.container_name)
            container.reload()
            status = container.status
            if status == "running":
                if self.restart_if_running:
                    print(
                        f"Container {self.container_name} is already running. Restarting ..."
                    )
                    container.remove(force=True)
                else:
                    print(
                        f"Container {self.container_name} is already running. Reusing ..."
                    )
                    self._container = container
                    self._wait_until_ready()
                    print(
                        f"Container ready. Base URL: http://127.0.0.1:{self.host_port}"
                    )
                    return
            elif status == "exited" and self.reuse_stopped_container:
                print(
                    f"Container {self.container_name} is stopped. Reusing stopped container ..."
                )
                self._container = container
                self._container.start()
                print("Waiting for container to be ready ...")
                self._wait_until_ready()
                print(f"Container ready. Base URL: http://127.0.0.1:{self.host_port}")
                return
            else:
                print(
                    f"Container {self.container_name} is in status '{status}'. Removing ..."
                )
                container.remove(force=True)
        except NotFound:
            print("No existing container found.")

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
                cpu_shares=4096,
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

    def stop(self, remove_container=False) -> None:
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
            if remove_container:
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

    def duplicate(self, new_image_name: str) -> None:
        if not self._client:
            raise RuntimeError("Docker client not initialized.")
        if not self._container:
            raise RuntimeError("Container not initialized.")

        print(
            f"Committing container {self.container_name} to new image {new_image_name} ..."
        )
        try:
            image = self._container.commit(repository=new_image_name, tag="latest")
            print(f"Successfully created image {new_image_name} with ID {image.id}.")
        except APIError as e:
            raise RuntimeError(f"Failed to commit container to image: {e}") from e


_shutdown_once = threading.Event()


def start_service() -> DockerService:
    assert (
        DOCKER_CONFIG is not None
    ), "DOCKER_CONFIG must be defined in the configuration."
    assert isinstance(DOCKER_CONFIG.IMAGE, str), "DOCKER_CONFIG.IMAGE must be a string."
    assert isinstance(
        DOCKER_CONFIG.CONTAINER_NAME, str
    ), "DOCKER_CONFIG.CONTAINER_NAME must be a string."
    assert isinstance(
        DOCKER_CONFIG.HOST_PORT, int
    ), "DOCKER_CONFIG.HOST_PORT must be an integer."
    assert isinstance(
        DOCKER_CONFIG.CONTAINER_PORT, int
    ), "DOCKER_CONFIG.CONTAINER_PORT must be an integer."
    assert isinstance(
        DOCKER_CONFIG.READY_TIMEOUT, int
    ), "DOCKER_CONFIG.READY_TIMEOUT must be an integer."
    assert isinstance(
        DOCKER_CONFIG.RESTART_IF_RUNNING, bool
    ), "DOCKER_CONFIG.RESTART_IF_RUNNING must be a boolean."
    assert isinstance(
        DOCKER_CONFIG.REUSE_STOPPED_CONTAINER, bool
    ), "DOCKER_CONFIG.REUSE_STOPPED_CONTAINER must be a boolean."

    service = DockerService(
        image=DOCKER_CONFIG.IMAGE,
        container_name=DOCKER_CONFIG.CONTAINER_NAME,
        host_port=DOCKER_CONFIG.HOST_PORT,
        container_port=DOCKER_CONFIG.CONTAINER_PORT,
        ready_timeout_s=DOCKER_CONFIG.READY_TIMEOUT,
        restart_if_running=DOCKER_CONFIG.RESTART_IF_RUNNING,
        reuse_stopped_container=DOCKER_CONFIG.REUSE_STOPPED_CONTAINER,
    )

    assert isinstance(
        DOCKER_CONFIG.REMOVE_WHEN_STOPPED, bool
    ), "DOCKER_CONFIG.REMOVE_WHEN_STOPPED must be a boolean."
    assert isinstance(
        DOCKER_CONFIG.STOP_WHEN_END, bool
    ), "DOCKER_CONFIG.STOP_WHEN_END must be a boolean."
    remove_when_stopped = DOCKER_CONFIG.REMOVE_WHEN_STOPPED
    stop_when_end = DOCKER_CONFIG.STOP_WHEN_END

    def shutdown(reason: str) -> None:
        if _shutdown_once.is_set():
            return
        _shutdown_once.set()
        print(f"Shutting down ({reason}) ...")
        if stop_when_end:
            service.stop(remove_container=remove_when_stopped)

    atexit.register(shutdown, "atexit")

    def _handle_signal(signum, frame) -> None:
        shutdown(f"signal {signum}")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    service.start()

    return service


service = start_service()
