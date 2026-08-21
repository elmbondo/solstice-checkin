import pika
import os
import json
import time
import requests
import threading

QUEUE_NAME = "print_requests"
KIOSK_WEBHOOK_URL = "http://127.0.0.1:6002/webhook/print-complete"

def handle_print_job(ch, method, properties, body):
    data = json.loads(body)
    attendee_id = data["attendee_id"]
    print_id = data["print_id"]

    print("printing badge for", attendee_id)
    time.sleep(2)  # still pretending the printer is slow

    payload = {
        "event": "print.completed",
        "print_id": print_id,
        "attendee_id": attendee_id,
        "status": "success",
        "printed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    try:
        requests.post(KIOSK_WEBHOOK_URL, json=payload, timeout=5)
    except requests.RequestException as e:
        print("webhook call failed:", e)

    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consuming():
    params = pika.URLParameters(os.environ.get("AMQP_URL"))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=handle_print_job)

    print("waiting for print jobs...")
    channel.start_consuming()

if __name__ == "__main__":
    start_consuming()