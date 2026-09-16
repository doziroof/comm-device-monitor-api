from datetime import datetime

from flask import Blueprint, jsonify, request

from . import db

api = Blueprint("api", __name__)

OPS = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "=": lambda a, b: a == b,
}


def ok(data=None, message="ok"):
    return jsonify({"code": 0, "message": message, "data": data})


def err(message, http_code=400):
    return jsonify({"code": 1, "message": message, "data": None}), http_code


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def evaluate_alerts(device_id: str, metric: str, value: float, collected_at: str):
    rules = db.query_all(
        "SELECT id, operator, threshold, severity FROM alert_rules "
        "WHERE metric=%s AND enabled=1",
        (metric,),
    )
    created = []
    for rule in rules:
        fn = OPS.get(rule["operator"])
        if not fn:
            continue
        if fn(float(value), float(rule["threshold"])):
            message = f"{device_id} {metric}={value} 触发规则 {rule['operator']}{rule['threshold']}"
            db.execute(
                "INSERT INTO alerts "
                "(device_id, metric, value, rule_id, severity, message, triggered_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (
                    device_id,
                    metric,
                    value,
                    rule["id"],
                    rule["severity"],
                    message,
                    collected_at,
                ),
            )
            created.append(
                {
                    "rule_id": rule["id"],
                    "severity": rule["severity"],
                    "message": message,
                }
            )
    return created


@api.get("/health")
def health():
    return ok({"service": "comm-device-monitor-api", "time": now_str()})


@api.get("/api/devices")
def list_devices():
    status = request.args.get("status", type=int)
    sql = "SELECT * FROM devices"
    args = []
    if status is not None:
        sql += " WHERE status=%s"
        args.append(status)
    sql += " ORDER BY id DESC"
    return ok(db.query_all(sql, args))


@api.post("/api/devices")
def create_device():
    body = request.get_json(silent=True) or {}
    device_id = body.get("device_id")
    name = body.get("name")
    if not device_id or not name:
        return err("device_id 与 name 必填")
    exists = db.query_one(
        "SELECT id FROM devices WHERE device_id=%s", (device_id,)
    )
    if exists:
        return err("device_id 已存在", 409)
    db.execute(
        "INSERT INTO devices (device_id, name, type, location, status) "
        "VALUES (%s,%s,%s,%s,%s)",
        (
            device_id,
            name,
            body.get("type"),
            body.get("location"),
            int(body.get("status", 1)),
        ),
    )
    return ok(db.query_one("SELECT * FROM devices WHERE device_id=%s", (device_id,)))


@api.get("/api/devices/<device_id>")
def get_device(device_id):
    row = db.query_one("SELECT * FROM devices WHERE device_id=%s", (device_id,))
    if not row:
        return err("设备不存在", 404)
    return ok(row)


@api.patch("/api/devices/<device_id>")
def update_device(device_id):
    row = db.query_one("SELECT * FROM devices WHERE device_id=%s", (device_id,))
    if not row:
        return err("设备不存在", 404)
    body = request.get_json(silent=True) or {}
    fields = []
    args = []
    for key in ("name", "type", "location", "status"):
        if key in body:
            fields.append(f"{key}=%s")
            args.append(body[key])
    if not fields:
        return err("没有可更新字段")
    args.append(device_id)
    db.execute(f"UPDATE devices SET {', '.join(fields)} WHERE device_id=%s", args)
    return ok(db.query_one("SELECT * FROM devices WHERE device_id=%s", (device_id,)))


def _insert_metric(item):
    device_id = item.get("device_id")
    metric = item.get("metric")
    value = item.get("value")
    if not device_id or not metric or value is None:
        return None, "device_id、metric、value 必填"
    device = db.query_one(
        "SELECT id FROM devices WHERE device_id=%s", (device_id,)
    )
    if not device:
        return None, f"设备不存在: {device_id}"
    collected_at = item.get("collected_at") or now_str()
    db.execute(
        "INSERT INTO metrics (device_id, metric, value, unit, collected_at) "
        "VALUES (%s,%s,%s,%s,%s)",
        (device_id, metric, float(value), item.get("unit"), collected_at),
    )
    alerts = evaluate_alerts(device_id, metric, float(value), collected_at)
    return {
        "device_id": device_id,
        "metric": metric,
        "value": float(value),
        "collected_at": collected_at,
        "alerts": alerts,
    }, None


@api.post("/api/metrics")
def create_metric():
    body = request.get_json(silent=True) or {}
    data, error = _insert_metric(body)
    if error:
        return err(error)
    return ok(data)


@api.post("/api/metrics/batch")
def create_metrics_batch():
    body = request.get_json(silent=True) or {}
    items = body.get("items")
    if not isinstance(items, list) or not items:
        return err("items 必须是非空数组")
    results = []
    errors = []
    for idx, item in enumerate(items):
        data, error = _insert_metric(item)
        if error:
            errors.append({"index": idx, "message": error})
        else:
            results.append(data)
    return ok({"inserted": results, "errors": errors})


@api.get("/api/metrics")
def list_metrics():
    sql = "SELECT * FROM metrics WHERE 1=1"
    args = []
    device_id = request.args.get("device_id")
    metric = request.args.get("metric")
    start = request.args.get("start")
    end = request.args.get("end")
    limit = request.args.get("limit", default=100, type=int)
    if device_id:
        sql += " AND device_id=%s"
        args.append(device_id)
    if metric:
        sql += " AND metric=%s"
        args.append(metric)
    if start:
        sql += " AND collected_at>=%s"
        args.append(start)
    if end:
        sql += " AND collected_at<=%s"
        args.append(end)
    sql += " ORDER BY collected_at DESC, id DESC LIMIT %s"
    args.append(max(1, min(limit, 1000)))
    return ok(db.query_all(sql, args))


@api.get("/api/alert-rules")
def list_rules():
    return ok(db.query_all("SELECT * FROM alert_rules ORDER BY id"))


@api.post("/api/alert-rules")
def create_rule():
    body = request.get_json(silent=True) or {}
    metric = body.get("metric")
    operator = body.get("operator")
    threshold = body.get("threshold")
    if not metric or operator not in OPS or threshold is None:
        return err("metric、operator、threshold 必填，operator 需为 > >= < <= =")
    db.execute(
        "INSERT INTO alert_rules (metric, operator, threshold, severity, enabled) "
        "VALUES (%s,%s,%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE severity=VALUES(severity), enabled=VALUES(enabled)",
        (
            metric,
            operator,
            float(threshold),
            body.get("severity", "warning"),
            int(body.get("enabled", 1)),
        ),
    )
    row = db.query_one(
        "SELECT * FROM alert_rules WHERE metric=%s AND operator=%s AND threshold=%s",
        (metric, operator, float(threshold)),
    )
    return ok(row)


@api.get("/api/alerts")
def list_alerts():
    sql = "SELECT * FROM alerts WHERE 1=1"
    args = []
    device_id = request.args.get("device_id")
    if device_id:
        sql += " AND device_id=%s"
        args.append(device_id)
    sql += " ORDER BY triggered_at DESC, id DESC LIMIT %s"
    args.append(request.args.get("limit", default=100, type=int))
    return ok(db.query_all(sql, args))
