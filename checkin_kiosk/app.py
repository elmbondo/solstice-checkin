from flask import Flask, request, jsonify
import sqlite3
import requests

app = Flask(__name__)

DB_PATH = "checkins.db"
PRINTER_URL = "http://127.0.0.1:6001/print"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            attendee_id TEXT PRIMARY KEY,
            checked_in_at TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/checkin", methods=["POST"])
def checkin():
    data = request.get_json()
    attendee_id = data.get("attendee_id")
    if not attendee_id:
        return jsonify({"error": "attendee_id required"}), 400

    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute("SELECT attendee_id FROM checkins WHERE attendee_id = ?", (attendee_id,)).fetchone()

    if existing:
        conn.close()
        return jsonify({"status": "already_checked_in", "attendee_id": attendee_id}), 409

    try:
        r = requests.post(PRINTER_URL, json={"attendee_id": attendee_id}, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        conn.close()
        return jsonify({"status": "print_failed", "error": str(e)}), 502

    conn.execute("INSERT INTO checkins (attendee_id, checked_in_at) VALUES (?, datetime('now'))", (attendee_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "checked_in", "attendee_id": attendee_id})

if __name__ == "__main__":
    init_db()
    app.run(port=6002, debug=True)