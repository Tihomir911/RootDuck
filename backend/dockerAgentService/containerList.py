import docker
_client - docker.from_enw()

def list_containers() -> list[dict]:
    
    containers = _client.containers.list(all=True)
    
    result = []

    for container in containers:
        result.append({
            "id": container.id,
           
            "name": container.name,
            
            "image": container.image.tags[0] if container.image.tags else container.image.short_id,
            
            "status": container.status,
        })

    return result