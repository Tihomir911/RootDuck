import docker

_client = docker.from_env()

def restart_container(container_id: str) -> None:
    container = _client.containers.get(container_id)
    container.restart(timeout=10)

def stop_container(container_id: str) -> None:
    container = _client.containers.get(container_id)
    container.stop(timeout=10)

def start_container(container_id: str) -> None:
    container = _client.containers.get(container_id)
    container.start()