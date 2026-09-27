import time

import psutil


def collect_system_metrics() -> dict:
  
    cpu_per_core = psutil.cpu_percent(percpu=True, interval=0.1)

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    network = psutil.net_io_counters()

    raw_temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
    temperatures = {}
    for chip_name, entries in raw_temps.items():
       
        for index, entry in enumerate(entries):
            label = entry.label or f"{chip_name}_{index}"
            temperatures[label] = entry.current

    return {
        "timestamp": time.time(),
        "cpu_per_core": cpu_per_core,
        "cpu_average": sum(cpu_per_core) / len(cpu_per_core) if cpu_per_core else 0.0,
        "memory_used_mb": round(memory.used / (1024 * 1024), 1),
        "memory_total_mb": round(memory.total / (1024 * 1024), 1),
        "memory_percent": memory.percent,
        "disk_used_gb": round(disk.used / (1024 ** 3), 1),
        "disk_total_gb": round(disk.total / (1024 ** 3), 1),
        "disk_percent": disk.percent,
        "network_bytes_sent": network.bytes_sent,
        "network_bytes_recv": network.bytes_recv,
        "temperatures": temperatures,
    }