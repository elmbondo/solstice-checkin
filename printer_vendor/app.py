from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route("/print", methods=["POST"])
def print_badge():
    data = request.get_json()
    attendee_id = data.get("attendee_id")
    if not attendee_id:
        return jsonify({"error": "attendee_id required"}), 400

    time.sleep(2)  # pretend the printer is slow

    print("printed:", attendee_id)
    return jsonify({"status": "success", "attendee_id": attendee_id})

if __name__ == "__main__":
    app.run(port=6001, debug=True)