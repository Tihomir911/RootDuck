
import docker
from fastapi import FastAPI, HTTPException

from containerList import list_containers
from containerStats import get_container_stats
from containerControl import restart_container, stop_container, start_container

app = FastAPI(title="RootDuck Docker Agent Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/containers")
def get_containers():
    return list_containers()


@app.get("/containers/{container_id}/stats")
def get_stats(container_id: str):
    try:
        return get_container_stats(container_id)
    except docker.errors.NotFound:
        
        raise HTTPException(status_code=404, detail="Container not found")


@app.post("/containers/{container_id}/restart")
def restart(container_id: str):
    try:
        restart_container(container_id)
        return {"status": "restarted"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")


@app.post("/containers/{container_id}/stop")
def stop(container_id: str):
    try:
        stop_container(container_id)
        return {"status": "stopped"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")


@app.post("/containers/{container_id}/start")
def start(container_id: str):
    try:
        start_container(container_id)
        return {"status": "started"}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")