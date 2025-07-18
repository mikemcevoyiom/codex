import os
import json
from datetime import datetime
from pathlib import Path
from influxdb_client import InfluxDBClient, Point, WriteOptions

INFLUX_HOST = os.getenv("INFLUX_HOST", "http://192.168.1.28:8086")
INFLUX_BUCKET = "Video_Convert"
INFLUX_ORG = os.getenv("INFLUX_ORG", "my-org")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")

DOCUMENTS_DIR = Path.home() / "Documents"
STATUS_FILES = [
    "convert.json",
    "streams.json",
]


def find_status_file(name: str) -> Path:
    """Return the path to a status file regardless of case."""
    path = DOCUMENTS_DIR / name
    if path.exists():
        return path
    lower = name.lower()
    for candidate in DOCUMENTS_DIR.glob("*.json"):
        if candidate.name.lower() == lower:
            return candidate
    return path


def load_entries(path):
    if not path.exists():
        print(f"Status log {path} not found")
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def send_entries(entries, measurement, write_api):
    for entry in entries:
        point = Point(measurement)
        for key, value in entry.items():
            if key == "time":
                try:
                    point.time(datetime.fromisoformat(str(value)))
                except Exception:
                    point.field("time_str", str(value))
            elif isinstance(value, (int, float)):
                point.field(key, value)
            else:
                point.tag(key, str(value))
        write_api.write(bucket=INFLUX_BUCKET, record=point)


def main():
    if not INFLUX_TOKEN:
        raise RuntimeError("INFLUX_TOKEN environment variable is not set")

    with InfluxDBClient(url=INFLUX_HOST, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        with client.write_api(
            write_options=WriteOptions(batch_size=1, flush_interval=1000)
        ) as write_api:
            for fname in STATUS_FILES:
                path = find_status_file(fname)
                entries = load_entries(path)
                if not entries:
                    print(f"No entries found in {path}")
                    continue
                measurement = Path(fname).stem
                send_entries(entries, measurement, write_api)
                print(
                    f"Uploaded {len(entries)} records from {fname} to {INFLUX_BUCKET}"
                )


if __name__ == "__main__":
    main()
