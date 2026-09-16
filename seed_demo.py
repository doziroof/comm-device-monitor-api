"""写入演示设备、指标与告警，便于本地验收。"""

from datetime import datetime, timedelta

from app import db


def main():
    devices = [
        ("BTS-001", "宏站-中山路", "macro", "南京"),
        ("BTS-002", "室分-软件园A", "indoor", "南京"),
        ("BTS-003", "微站-地铁口", "smallcell", "苏州"),
    ]
    for device_id, name, dtype, location in devices:
        exists = db.query_one(
            "SELECT id FROM devices WHERE device_id=%s", (device_id,)
        )
        if exists:
            continue
        db.execute(
            "INSERT INTO devices (device_id, name, type, location, status) "
            "VALUES (%s,%s,%s,%s,1)",
            (device_id, name, dtype, location),
        )
        print(f"inserted device {device_id}")

    base = datetime.now().replace(microsecond=0)
    samples = [
        ("BTS-001", "rsrp_dbm", -105.0, "dBm", 0),
        ("BTS-001", "rsrp_dbm", -112.5, "dBm", 5),
        ("BTS-001", "cpu_percent", 42.0, "%", 0),
        ("BTS-001", "cpu_percent", 91.0, "%", 8),
        ("BTS-002", "rsrp_dbm", -98.0, "dBm", 2),
        ("BTS-003", "cpu_percent", 55.0, "%", 3),
    ]
    for device_id, metric, value, unit, offset_min in samples:
        collected_at = (base - timedelta(minutes=offset_min)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        db.execute(
            "INSERT INTO metrics (device_id, metric, value, unit, collected_at) "
            "VALUES (%s,%s,%s,%s,%s)",
            (device_id, metric, value, unit, collected_at),
        )
        print(f"inserted metric {device_id} {metric}={value}")

    print("done. start API with: python run.py")


if __name__ == "__main__":
    main()
