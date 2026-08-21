**Solstice Events - Check-In Kiosk**

Meridian Pivot sprint (PLP), Solstice Events Co. scenario.

**Current architecture (post-pivot)**
- `printer_vendor/` - badge-printer vendor. No longer a web server; consumes print jobs from a RabbitMQ queue (`print_requests`) and calls back to the kiosk's webhook once printing completes.
- `checkin_kiosk/` - kiosk service (port 6002). On scan, immediately records a `pending` check-in and publishes a print request to the queue, rather than waiting on the printer directly.
  - `POST /checkin` - scan an attendee, returns `pending` immediately
  - `POST /webhook/print-complete` - called by the printer vendor once a print job finishes
  - `GET /status/<attendee_id>` - check current status (`pending` / `confirmed`)

**Behavior**
- First scan: check-in recorded as `pending`, print request queued, badge prints asynchronously, webhook flips status to `confirmed`.
- Repeat scan of a `pending` or `confirmed` attendee: rejected immediately, no new print job queued. Duplicate protection holds even while a request is still in flight.

**Running locally**
1. Create and activate a virtual environment, then `pip install flask requests pika`
2. Set `AMQP_URL` in each terminal to a RabbitMQ connection string (CloudAMQP free tier works)
3. Terminal 1: `cd printer_vendor && python app.py`
4. Terminal 2: `cd checkin_kiosk && python app.py`
5. POST to `http://127.0.0.1:6002/checkin` with JSON body `{"attendee_id": "ATT-001"}`

**History
This service originally called the printer vendor synchronously and waited for a success response before confirming check-in. The vendor deprecated that synchronous API, forcing a pivot to an async, queue-and-webhook model. See `SCOPE_DELTA.md` for the full breakdown of what changed.