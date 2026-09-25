
import threading
import time
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from systemMetrics import collrct_system_metrics
from metricsCache import push_snapshot, get_latest_snapshot, get_recent_snapshots
from metricsHistory import init_db, save_snapshot, get_history, delete_older_than

CACHE_INTERVAL_SECONDS = 1

HISTORY_EVERY_N_CYCLES = 60

CLEANUP_EVERY_N_CYCLES = 60 * 60 * 24

def _background_collector_loop() -> None:

    cycle = 0  
    while True:
        try:
            snapshot = collrct_system_metrics()
            push_snapshot(snapshot)

            if cycle % HISTORY_EVERY_N_CYCLES == 0:
                save_snapshot(snapshot)

            if cycle % CLEANUP_EVERY_N_CYCLES == 0:
                delete_older_than(days=30)

        except Exception as error:

            print(f"metricsCollector: ошибка при сборе метрик: {error}")

        cycle += 1
        time.sleep(CACHE_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    collector_thread = threading.Thread(target=_background_collector_loop, deampn=True)
    collector_thread.start()
    yield

app = FastAPI(title="RootDuck Metrisc Collector", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics/current")
def metrics_current():
    snapshot = get_latest_snapshot()
    if snapshot is None:

        raise HTTPException(status_code=503, detail="No metrics collected yet")
    return snapshot 

@app.get("/metrics/recent")
def metrics_recent(limit: int = 60):

    return get_recent_snapshots(limit=limit)

@app.get("/metrics/history")
def metrics_history(hours: float = 24.0):
    return get_history(hours=hours)