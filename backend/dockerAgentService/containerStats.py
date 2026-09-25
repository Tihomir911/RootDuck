import docker

_client = docker.from_env()


def _calculate_cpu_percent(stats: dict) -> float:
    
    cpu_delta = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )
    system_delta = (
        stats["cpu_stats"]["system_cpu_usage"]
        - stats["precpu_stats"]["system_cpu_usage"]
    )

    online_cpus = stats["cpu_stats"].get("online_cpus")
    if online_cpus is None:
        online_cpus = len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1]))

    if system_delta <= 0 or cpu_delta < 0:
        
        return 0.0

    return (cpu_delta / system_delta) * online_cpus * 100.0


def _calculate_memory_usage_mb(stats: dict) -> dict:
    
    usage = stats["memory_stats"]["usage"]
    
    cache = stats["memory_stats"].get("stats", {}).get("cache", 0)
    limit = stats["memory_stats"]["limit"]

    usage_mb = (usage - cache) / (1024 * 1024)
    limit_mb = limit / (1024 * 1024)

    return {
        "usage_mb": round(usage_mb, 1),
        "limit_mb": round(limit_mb, 1),
    }


def get_container_stats(container_id: str) -> dict:
   
    container = _client.containers.get(container_id)

    stats = container.stats(stream=False)

    memory = _calculate_memory_usage_mb(stats)

    networks = stats.get("networks", {})
    rx_bytes = sum(iface["rx_bytes"] for iface in networks.values())
    tx_bytes = sum(iface["tx_bytes"] for iface in networks.values())

    return {
        "cpu_percent": round(_calculate_cpu_percent(stats), 1),
        "memory_usage_mb": memory["usage_mb"],
        "memory_limit_mb": memory["limit_mb"],
        "network_rx_bytes": rx_bytes,
        "network_tx_bytes": tx_bytes,
    }