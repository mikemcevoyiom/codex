import os
import json
from pathlib import Path
from influxdb_client import InfluxDBClient, Point, WriteOptions

INFLUX_URL = os.getenv("INFLUX_URL", "http://192.168.1.28:8086")
INFLUX_BUCKET = "Video_Convert"
INFLUX_ORG = os.getenv("INFLUX_ORG", "my-org")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")

STATUS_PATH = Path.home() / "Documents" / "conversion_status.json"


def load_entries(path):
    if not path.exists():
        print(f"Status log {path} not found")
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def send_to_influxdb(entries):
    if not INFLUX_TOKEN:
        raise RuntimeError("INFLUX_TOKEN environment variable is not set")
    with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        write_api = client.write_api(write_options=WriteOptions(batch_size=1, flush_interval=1000))
        for entry in entries:
            point = (
                Point("video_conversion")
                .tag("status", entry.get("status", ""))
                .field("input", entry.get("input", ""))
                .field("output", entry.get("output", ""))
                .field("before_codec", entry.get("before_codec", ""))
                .field("after_codec", entry.get("after_codec", ""))
                .field("before_size", int(entry.get("before_size", 0)))
                .field("after_size", int(entry.get("after_size", 0)))
            )
            write_api.write(bucket=INFLUX_BUCKET, record=point)


def main():
    entries = load_entries(STATUS_PATH)
    if entries:
        send_to_influxdb(entries)
        print(f"Uploaded {len(entries)} records to {INFLUX_BUCKET}")


if __name__ == "__main__":
    main()
