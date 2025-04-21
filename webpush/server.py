import json
import os

import sentry_sdk
from constants import Office, Services
from flask import Flask, jsonify, request
from flask_cors import CORS
from models import Base, SessionLocal, WebPushSubscription, engine
from py_vapid.main import Vapid02, serialization
from pywebpush import WebPushException, webpush

SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=False,
    )

app = Flask(__name__)
CORS(app)

# Ensure database tables are created
Base.metadata.create_all(engine)

VAPID_PRIVATE_KEY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "private_key.pem"
)
VAPID_PUBLIC_KEY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "public_key.pem"
)


@app.route("/public_key", methods=["GET"])
def public_key():
    vapid = Vapid02.from_file(VAPID_PRIVATE_KEY)
    raw_pub = vapid.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    # Return the public key as a list of integers for direct Uint8Array conversion on the client
    return jsonify({"public_key": list(raw_pub)})


@app.route("/subscribe", methods=["POST"])
def subscribe():
    subscription = request.get_json()
    if not subscription:
        return jsonify({"error": "Subscription missing"}), 400

    # Extract fields from subscription
    endpoint = subscription.get("endpoint")
    keys = subscription.get("keys", {})
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    # Now services and offices are arrays of ID strings
    services = ",".join(map(str, subscription.get("services", [])))
    offices = ",".join(map(str, subscription.get("offices", [])))
    datetimes = subscription.get("datetimes", "")

    if not endpoint or not p256dh or not auth:
        return jsonify({"error": "Missing required subscription fields."}), 400

    with SessionLocal() as db:
        # Check if subscription already exists
        existing = (
            db.query(WebPushSubscription)
            .filter(WebPushSubscription.endpoint == endpoint)
            .one_or_none()
        )
        if existing:
            # Update existing subscription
            existing.p256dh = p256dh
            existing.auth = auth
            existing.services = services
            existing.offices = offices
            existing.datetimes = datetimes
            db.commit()
            return jsonify({"status": "subscription updated"}), 200

        new_sub = WebPushSubscription(
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            services=services,
            offices=offices,
            datetimes=datetimes,
        )
        db.add(new_sub)
        db.commit()
    return jsonify({"status": "subscribed"}), 201


@app.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    data = request.get_json()
    if not data or not data.get("endpoint"):
        return jsonify({"error": "Subscription endpoint missing."}), 400

    endpoint = data.get("endpoint")
    with SessionLocal() as db:
        sub = (
            db.query(WebPushSubscription)
            .filter(WebPushSubscription.endpoint == endpoint)
            .one_or_none()
        )
        if not sub:
            return jsonify({"error": "Subscription not found."}), 404
        db.delete(sub)
        db.commit()
    return jsonify({"status": "unsubscribed"}), 200


@app.route("/test_notification", methods=["POST"])
def test():
    data = request.get_json()
    if not data or not data.get("endpoint"):
        return jsonify({"error": "Subscription endpoint missing."}), 400

    endpoint = data.get("endpoint")
    with SessionLocal() as db:
        sub = (
            db.query(WebPushSubscription)
            .filter(WebPushSubscription.endpoint == endpoint)
            .one_or_none()
        )
    if not sub:
        return jsonify({"error": "Subscription not found."}), 404

    # Convert service and office IDs back to readable names for the test notification
    service_ids = sub.services.split(",") if sub.services else []
    office_ids = sub.offices.split(",") if sub.offices else []

    service_names = []
    office_names = []

    # Find service names
    for service_id in service_ids:
        if service_id:
            try:
                for service in Services:
                    if str(service.value) == service_id:
                        service_names.append(service.name)
                        break
            except ValueError:
                service_names.append(f"Unknown({service_id})")

    # Find office names
    for office_id in office_ids:
        if office_id:
            try:
                for office in Office:
                    if str(office.office_id) == office_id:
                        office_names.append(office.verbose_name)
                        break
            except ValueError:
                office_names.append(f"Unknown({office_id})")

    message = {
        "title": "Test Notification",
        "message": json.dumps(
            {
                "offices": office_names,
                "services": service_names,
                "datetimes": sub.datetimes.split(",") if sub.datetimes else [],
            }
        ),
    }

    try:
        # Convert subscription record into expected dict format
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
        }
        print("Send test notification to:", subscription_info)
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(message),
            vapid_private_key=VAPID_PRIVATE_KEY,
            ttl=600,
            vapid_claims={},
        )
        return jsonify({"status": "message sent"})
    except WebPushException as ex:
        print(f"Web push failed: {repr(ex)}")
        return jsonify({"error": str(ex)}), 500
