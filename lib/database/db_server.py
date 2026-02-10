import os

import psycopg2
from dotenv import load_dotenv
import json
from datetime import datetime, timezone
from flask import Flask, jsonify, request

from lib.database.constants import DB_QUERY_STATUS

load_dotenv()

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
    "dbname": os.getenv("PG_DATABASE"),
    "connect_timeout": 0,  # Set timeout to 5 seconds
}

# Connect to Database
try:
    db = psycopg2.connect(**DB_CONFIG)
    db.autocommit = True
    print("Database connected")
except Exception as e:
    print("Database connection error:", e)
    # exit(-1)


def query(text, params=None):
    """Execute SQL queries and return the results"""
    try:
        with db.cursor() as cursor:
            cursor.execute(text, params or ())

            # Handle each of the SQL queries
            query_type = text.lstrip().split()[0].upper()

            if query_type in ("SELECT", "EXPLAIN", "SHOW"):
                return DB_QUERY_STATUS.EXECUTION_SUCCESSFUL, cursor.fetchall()

            elif query_type in ("INSERT", "UPDATE", "DELETE"):
                return DB_QUERY_STATUS.EXECUTION_SUCCESSFUL, cursor.rowcount

            return DB_QUERY_STATUS.EXECUTION_SUCCESSFUL
    except Exception as e:
        print("Database query error:", e)
        return DB_QUERY_STATUS.EXECUTION_FAILED


# ---------------------------------------------------------------------------
# REST API routes (consumed by GSW-Frontend)
# ---------------------------------------------------------------------------

TELEMETRY_TYPE_MAP = {
    "heartbeat": 1,
    "nominal": 5,
    "hal": 2,
    "storage": 3,
}

COMMAND_NAMES = {
    0x40: "FORCE_REBOOT",
    0x41: "SWITCH_TO_STATE",
    0x42: "UPLINK_TIME_REFERENCE",
    0x43: "UPLINK_ORBIT_REFERENCE",
    0x44: "TURN_OFF_PAYLOAD",
    0x45: "SCHEDULE_OD_EXPERIMENT",
    0x46: "REQUEST_TM_NOMINAL",
    0x47: "REQUEST_TM_HAL",
    0x48: "REQUEST_TM_STORAGE",
    0x49: "REQUEST_TM_PAYLOAD",
    0x4A: "FILE_METADATA",
    0x4B: "FILE_PKT",
    0x50: "DOWNLINK_ALL_FILES",
}


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ---- Telemetry ---------------------------------------------------------

@app.route("/api/telemetry/latest/<tm_type>")
def api_telemetry_latest(tm_type):
    rx_id = TELEMETRY_TYPE_MAP.get(tm_type)
    if rx_id is None:
        return jsonify({"error": "Invalid type. Use: heartbeat, nominal, hal, storage"}), 400

    result = query(
        "SELECT rx_name, rx_id, rx_type, rx_data FROM rxData_tb "
        "WHERE rx_id = %s ORDER BY ctid DESC LIMIT 1;",
        (rx_id,),
    )
    if result == DB_QUERY_STATUS.EXECUTION_FAILED:
        return jsonify({"error": "Database error"}), 500
    if result[0] != DB_QUERY_STATUS.EXECUTION_SUCCESSFUL or not result[1]:
        return jsonify({"error": "No data found"}), 404

    row = result[1][0]
    return jsonify({
        "rx_name": row[0],
        "rx_id": row[1],
        "rx_type": row[2],
        "rx_data": row[3],
    })


@app.route("/api/telemetry/history")
def api_telemetry_history():
    tm_type = request.args.get("type", "nominal")
    rx_id = TELEMETRY_TYPE_MAP.get(tm_type)
    if rx_id is None:
        return jsonify({"error": "Invalid type"}), 400

    page = max(1, request.args.get("page", 1, type=int))
    limit = min(100, max(1, request.args.get("limit", 50, type=int)))
    offset = (page - 1) * limit

    result = query(
        "SELECT rx_name, rx_id, rx_type, rx_data FROM rxData_tb "
        "WHERE rx_id = %s ORDER BY ctid DESC LIMIT %s OFFSET %s;",
        (rx_id, limit, offset),
    )
    if result == DB_QUERY_STATUS.EXECUTION_FAILED:
        return jsonify({"error": "Database error"}), 500

    rows = result[1] if result[0] == DB_QUERY_STATUS.EXECUTION_SUCCESSFUL else []

    count_result = query(
        "SELECT COUNT(*) FROM rxData_tb WHERE rx_id = %s;", (rx_id,)
    )
    total = 0
    if count_result != DB_QUERY_STATUS.EXECUTION_FAILED and count_result[1]:
        total = count_result[1][0][0]

    data = []
    for row in rows:
        data.append({
            "rx_name": row[0],
            "rx_id": row[1],
            "rx_type": row[2],
            "rx_data": row[3],
        })

    return jsonify({"data": data, "page": page, "limit": limit, "total": total})


# ---- Commands -----------------------------------------------------------

@app.route("/api/commands/queue", methods=["GET"])
def api_commands_queue_get():
    result = query("SELECT * FROM public.txcommands_tb ORDER BY created_at ASC;")
    if result == DB_QUERY_STATUS.EXECUTION_FAILED:
        return jsonify({"error": "Database error"}), 500

    rows = result[1] if result[0] == DB_QUERY_STATUS.EXECUTION_SUCCESSFUL else []

    commands = []
    for row in rows:
        cmd_id = row[1]
        commands.append({
            "id": row[0],
            "command_id": cmd_id,
            "command_name": COMMAND_NAMES.get(cmd_id, f"CMD_{cmd_id}"),
            "created_at": str(row[2]) if row[2] else None,
            "args": row[3] if row[3] else {},
        })

    return jsonify(commands)


@app.route("/api/commands/queue", methods=["POST"])
def api_commands_queue_post():
    data = request.get_json(silent=True)
    if not data or "command_id" not in data:
        return jsonify({"error": "command_id is required"}), 400

    command_id = data["command_id"]
    args = data.get("args", {})

    result = query(
        "INSERT INTO txcommands_tb (command_id, args) VALUES (%s, %s);",
        (command_id, json.dumps(args)),
    )
    if result == DB_QUERY_STATUS.EXECUTION_FAILED:
        return jsonify({"success": False, "error": "Insert failed"}), 500

    return jsonify({"success": True}), 201


@app.route("/api/commands/queue/<int:cmd_id>", methods=["DELETE"])
def api_commands_queue_delete(cmd_id):
    result = query("DELETE FROM txcommands_tb WHERE id = %s;", (cmd_id,))
    if result == DB_QUERY_STATUS.EXECUTION_FAILED:
        return jsonify({"success": False, "error": "Delete failed"}), 500

    return jsonify({"success": True})


@app.route("/api/commands/estop", methods=["POST"])
def api_commands_estop():
    result = query(
        "INSERT INTO txcommands_tb (command_id, args, created_at) "
        "VALUES (%s, %s, %s);",
        (0x40, "{}", "1970-01-01T00:00:00+00:00"),
    )
    if result == DB_QUERY_STATUS.EXECUTION_FAILED:
        return jsonify({"success": False, "error": "E-STOP failed"}), 500

    return jsonify({"success": True, "message": "E-STOP FORCE_REBOOT queued"})


# ---- System -------------------------------------------------------------

@app.route("/api/system/link-status")
def api_system_link_status():
    result = query(
        "SELECT rx_name, rx_id, rx_data FROM rxData_tb ORDER BY ctid DESC LIMIT 1;"
    )
    if result == DB_QUERY_STATUS.EXECUTION_FAILED or not result[1]:
        return jsonify({
            "status": "disconnected",
            "last_contact": None,
            "last_tm_age_seconds": None,
        })

    return jsonify({"status": "connected"})


@app.route("/api/system/health")
def api_system_health():
    try:
        result = query("SELECT 1;")
        db_ok = result != DB_QUERY_STATUS.EXECUTION_FAILED
    except Exception:
        db_ok = False

    return jsonify({"status": "ok", "database": "connected" if db_ok else "disconnected"})
