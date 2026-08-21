from flask import Flask, request, jsonify
import sqlite3
import pika
import os
import uuid
import json

app = Flask(__name__)

DB_PATH = "checkins.db"
QUEUE_NAME = "print_requests"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            attendee_id TEXT PRIMARY KEY,
            print_id TEXT,
            status TEXT,
            requested_at TEXT,
            checked_in_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def publish_print_request(attendee_id, print_id):
    params = pika.URLParameters(os.environ.get("AMQP_URL"))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    payload = json.dumps({"attendee_id": attendee_id, "print_id": print_id})
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=payload)
    connection.close()

@app.route("/checkin", methods=["POST"])
def checkin():
    data = request.get_json()
    attendee_id = data.get("attendee_id")
    if not attendee_id:
        return jsonify({"error": "attendee_id required"}), 400

    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute("SELECT status FROM checkins WHERE attendee_id = ?", (attendee_id,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"status": existing[0], "attendee_id": attendee_id}), 409

    print_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO checkins (attendee_id, print_id, status, requested_at) VALUES (?, ?, 'pending', datetime('now'))",
        (attendee_id, print_id)
    )
    conn.commit()
    conn.close()

    publish_print_request(attendee_id, print_id)
    print("queued print for", attendee_id)

    return jsonify({"status": "pending", "attendee_id": attendee_id, "print_id": print_id}), 202

@app.route("/webhook/print-complete", methods=["POST"])
def print_complete():
    data = request.get_json()
    print_id = data.get("print_id")
    attendee_id = data.get("attendee_id")
    status = data.get("status")

    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT print_id FROM checkins WHERE attendee_id = ? AND status = 'pending'", (attendee_id,)
    ).fetchone()

    if not row or row[0] != print_id:
        conn.close()
        return jsonify({"error": "no matching pending request"}), 404

    if status == "success":
        conn.execute(
            "UPDATE checkins SET status = 'confirmed', checked_in_at = datetime('now') WHERE attendee_id = ?",
            (attendee_id,)
        )
        conn.commit()

    conn.close()
    return jsonify({"received": True})

@app.route("/status/<attendee_id>")
def check_status(attendee_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT status FROM checkins WHERE attendee_id = ?", (attendee_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"attendee_id": attendee_id, "status": row[0]})

if __name__ == "__main__":
    init_db()
    app.run(port=6002, debug=True, use_reloader=False)