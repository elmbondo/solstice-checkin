**Solstice Events - Check-In Kiosk**



Baseline build for the Meridian Pivot sprint (PLP), Solstice Events Co. scenario.



**Services**

\- `printer\_vendor/` - mock badge-printer vendor, synchronous `/print` endpoint (port 6001)

\- `checkin\_kiosk/` - kiosk service, `/checkin` endpoint (port 6002). Calls the printer vendor synchronously and waits for success before marking an attendee as checked in.



**Behavior**

\- First scan of an attendee: prints badge, marks checked in.

\- Repeat scan of an already-checked-in attendee: rejected with `already\_checked\_in` (409), no reprint triggered.



**Running locally**

1\. Create and activate a virtual environment, then `pip install flask requests`

2\. Terminal 1: `cd printer\_vendor \&\& python app.py`

3\. Terminal 2: `cd checkin\_kiosk \&\& python app.py`

4\. POST to `http://127.0.0.1:6002/checkin` with JSON body `{"attendee\_id": "ATT-001"}`



This is the pre-pivot baseline. Solstice's printer vendor is deprecating this synchronous API, see the pivot documentation for the async/webhook rebuild.

