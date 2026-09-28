import json
import os
import sqlite3
import time
from pathlib import Path

DB_PATH = os.environ.get("METRICS_DB_PATH", "/data/metrics.db")

def _get_connection() -> sqlite3.Connection:

    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    
    connection = _get_connection()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS metrics_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            cpu_average REAL NOT NULL,
            memory_percent REAL NOT NULL,
            disk_percent REAL NOT NULL,
            raw_json TEXT NOT NULL
        )
    """)
    
    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
        ON metrics_history (timestamp)
    """)
    connection.commit()
    connection.close()


def save_snapshot(snapshot: dict) -> None:
    
    connection = _get_connection()
    connection.execute(
        """
        INSERT INTO metrics_history (timestamp, cpu_average, memory_percent, disk_percent, raw_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            snapshot["timestamp"],
            snapshot["cpu_average"],
            snapshot["memory_percent"],
            snapshot["disk_percent"],
            json.dumps(snapshot),
        ),
    )
    connection.commit()
    connection.close()


def get_history(hours: float = 24.0) -> list[dict]:
   
    since_timestamp = time.time() - hours * 3600

    connection = _get_connection()
    cursor = connection.execute(
        """
        SELECT raw_json FROM metrics_history
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
        """,
        (since_timestamp,),
    )
    rows = cursor.fetchall()
    connection.close()

    return [json.loads(row[0]) for row in rows]


def delete_older_than(days: float = 30.0) -> None:
   
    cutoff_timestamp = time.time() - days * 86400

    connection = _get_connection()
    connection.execute(
        "DELETE FROM metrics_history WHERE timestamp < ?",
        (cutoff_timestamp,),
    )
    connection.commit()
    connection.close()