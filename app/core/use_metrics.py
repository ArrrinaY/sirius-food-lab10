"""USE-метрики (Utilization, Saturation, Errors) процесса API и хоста.

Utilization — насколько занят ресурс (CPU, память, диск).
Saturation — насколько ресурс перегружен (load average, пул БД, очереди).
Errors — сколько ошибок (исключения, 5xx, сообщения в DLQ).

Значения обновляются на каждом scrape /metrics: фоновый поток не нужен,
а psutil.cpu_percent/Process.cpu_percent считают среднее с прошлого вызова.
"""
import os
import shutil
import threading
from pathlib import Path

import psutil
from prometheus_client import Counter, Gauge

from app.database import engine

CPU = Gauge("sirius_cpu_utilization_ratio", "CPU utilization, 0..1", ["scope"])
MEMORY_USED = Gauge("sirius_memory_used_bytes", "Memory used", ["scope"])
MEMORY_TOTAL = Gauge("sirius_memory_total_bytes", "Memory available to the host")
MEMORY_RATIO = Gauge("sirius_memory_utilization_ratio", "Memory utilization, 0..1", ["scope"])
LOAD = Gauge("sirius_load_average", "System load average", ["window"])
CPU_CORES = Gauge("sirius_cpu_cores", "CPU cores visible to the process")
THREADS = Gauge("sirius_process_threads", "Threads in the API process")
OPEN_FDS = Gauge("sirius_open_file_descriptors", "Open descriptors/handles in the API process")
DISK = Gauge("sirius_disk_utilization_ratio", "Disk utilization of the project drive, 0..1")
DB_POOL = Gauge("sirius_db_pool_connections", "SQLAlchemy pool connections", ["state"])

UNHANDLED_EXCEPTIONS = Counter(
    "sirius_unhandled_exceptions_total", "Unhandled exceptions in the API"
)

_process = psutil.Process()
_lock = threading.Lock()


def _set_utilization() -> None:
    cores = psutil.cpu_count() or 1
    CPU_CORES.set(cores)

    host_cpu = psutil.cpu_percent(interval=None) / 100
    CPU.labels(scope="host").set(min(max(host_cpu, 0.0), 1.0))

    # cpu_percent процесса может быть >100 на многоядерной машине.
    process_cpu = _process.cpu_percent(interval=None) / 100 / cores
    CPU.labels(scope="process").set(min(max(process_cpu, 0.0), 1.0))

    memory = psutil.virtual_memory()
    used = memory.total - memory.available
    MEMORY_TOTAL.set(memory.total)
    MEMORY_USED.labels(scope="host").set(used)
    MEMORY_RATIO.labels(scope="host").set(used / memory.total if memory.total else 0.0)

    rss = _process.memory_info().rss
    MEMORY_USED.labels(scope="process").set(rss)
    MEMORY_RATIO.labels(scope="process").set(rss / memory.total if memory.total else 0.0)


def _set_saturation() -> None:
    try:
        load1, load5, load15 = psutil.getloadavg()
    except (AttributeError, OSError):
        pass
    else:
        for window, value in (("1m", load1), ("5m", load5), ("15m", load15)):
            LOAD.labels(window=window).set(value)

    THREADS.set(_process.num_threads())
    try:
        handles = _process.num_handles()  # Windows
    except AttributeError:
        handles = _process.num_fds()  # Linux/macOS
    OPEN_FDS.set(handles)

    anchor = Path(os.getcwd()).anchor or os.sep
    disk = shutil.disk_usage(anchor)
    DISK.set(disk.used / disk.total if disk.total else 0.0)

    pool = engine.pool
    if hasattr(pool, "checkedout"):
        DB_POOL.labels(state="size").set(pool.size())
        DB_POOL.labels(state="checked_out").set(pool.checkedout())
        DB_POOL.labels(state="overflow").set(pool.overflow())


def collect_use_metrics() -> None:
    # Метрики не должны ломать scrape, даже если psutil/драйвер БД недоступны.
    with _lock:
        try:
            _set_utilization()
            _set_saturation()
        except Exception:
            pass
