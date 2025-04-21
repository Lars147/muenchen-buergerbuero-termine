#!/usr/bin/env python3
import json
import os
import subprocess
import time
from datetime import datetime

import schedule
from pywebpush import WebPushException, webpush

from webpush.constants import Office, Services
from webpush.models import Appointment, SessionLocal, WebPushSubscription

VAPID_PRIVATE_KEY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "webpush", "private_key.pem"
)


def notify_subscribers_of_new_appointments(new_appointments):
    """
    Send push notifications to subscribers when new appointments match their preferences

    Args:
        new_appointments: List of newly added Appointment objects
    """
    if not new_appointments:
        return

    print(
        f"[{datetime.now()}] Sending notifications for {len(new_appointments)} new appointments..."
    )

    try:
        with SessionLocal() as db:
            # Get all active subscriptions
            subscriptions = db.query(WebPushSubscription).all()

            if not subscriptions:
                print(f"[{datetime.now()}] No subscriptions found")
                return

            notifications_sent = 0

            for appointment in new_appointments:
                # Find subscriptions that match this appointment's criteria
                matching_subscriptions = []

                for sub in subscriptions:
                    # Parse subscription preferences from comma-separated strings
                    # Access the actual string value directly from the SQLAlchemy object
                    services_str = getattr(sub, "services", "")
                    offices_str = getattr(sub, "offices", "")

                    services = services_str.split(",") if services_str else []
                    offices = offices_str.split(",") if offices_str else []

                    # Check if this appointment matches the subscription preferences
                    # Now comparing IDs as strings (since they are stored as comma-separated strings in the DB)
                    matches = True

                    # Match office ID if specified in preferences
                    if offices and str(appointment.office_id) not in offices:
                        matches = False

                    # Match service ID if specified in preferences
                    if services and str(appointment.service_id) not in services:
                        matches = False

                    if matches:
                        matching_subscriptions.append(sub)

                # Send notifications to matching subscriptions
                for sub in matching_subscriptions:
                    try:
                        # Find service and office names for human-readable notification
                        service_name = "Unknown Service"
                        office_name = "Unknown Office"

                        # Get service name
                        for service in Services:
                            if service.value == appointment.service_id:
                                service_name = service.name
                                break

                        # Get office name
                        for office in Office:
                            if office.office_id == appointment.office_id:
                                office_name = office.verbose_name
                                break

                        # Create notification payload
                        payload = json.dumps(
                            {
                                "title": "New Appointment Available!",
                                "message": f"{service_name} at {office_name} on {appointment.date.strftime('%Y-%m-%d %H:%M')}",
                            }
                        )

                        # Get subscription info
                        subscription_info = {
                            "endpoint": sub.endpoint,
                            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                        }

                        # Send the notification
                        webpush(
                            subscription_info=subscription_info,
                            data=payload,
                            vapid_private_key=VAPID_PRIVATE_KEY,
                            vapid_claims={"sub": "mailto:your-email@example.com"},
                        )

                        notifications_sent += 1

                    except WebPushException as e:
                        print(
                            f"[{datetime.now()}] Web Push failed for subscription {sub.id}: {e}"
                        )

                        # If subscription is no longer valid (410 Gone), delete it
                        if (
                            hasattr(e, "response")
                            and e.response
                            and e.response.status_code == 410
                        ):
                            db.delete(sub)
                            db.commit()

                    except Exception as e:
                        print(f"[{datetime.now()}] Error sending notification: {e}")

            print(f"[{datetime.now()}] Sent {notifications_sent} notifications")

    except Exception as e:
        print(f"[{datetime.now()}] Error in notification system: {e}")


def run_appointment_fetcher():
    """
    Run the existing get_buergerbuero_appointments.py script to fetch appointments
    """
    print(f"[{datetime.now()}] Running appointment fetch job...")

    try:
        # Run the script to update appointments.json
        subprocess.run(["python", "get_buergerbuero_appointments.py"], check=True)
        print(f"[{datetime.now()}] Appointments fetched successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] Error running get_buergerbuero_appointments.py: {e}")
        return False


def sync_appointments_to_db():
    """
    Read the appointments.json file and sync data to the database
    """
    print(f"[{datetime.now()}] Syncing appointments to database...")

    if not os.path.exists("appointments.json"):
        print(f"[{datetime.now()}] appointments.json file not found")
        return False

    try:
        # Read the JSON file
        with open("appointments.json", "r") as file:
            data = json.load(file)

        # Use SessionLocal to create a new session
        with SessionLocal() as db:
            appointments_added = 0
            new_appointments = []

            # Process each service and office in the JSON data
            for service_name, offices in data.items():
                # Get service ID from service name
                service_id = None
                for service in Services:
                    if service.name == service_name:
                        service_id = service.value
                        break

                if service_id is None:
                    print(
                        f"[{datetime.now()}] Unknown service: {service_name}, skipping"
                    )
                    continue

                for office_name, dates in offices.items():
                    # Get office ID from office name
                    office_id = None
                    office_verbose_name = None
                    for office_enum in Office:
                        if office_enum.name == office_name:
                            office_id = office_enum.office_id
                            office_verbose_name = office_enum.verbose_name
                            break

                    if office_id is None:
                        print(
                            f"[{datetime.now()}] Unknown office: {office_name}, skipping"
                        )
                        continue

                    for date_str, appointment_data in dates.items():
                        # Skip entries that have errors or no appointment timestamps
                        if "appointmentTimestamps" not in appointment_data:
                            continue

                        # Process each timestamp for the date
                        for timestamp in appointment_data["appointmentTimestamps"]:
                            # Convert timestamp to datetime
                            appointment_datetime = datetime.fromtimestamp(timestamp)

                            # Check if this appointment already exists in the database
                            existing_appointment = (
                                db.query(Appointment)
                                .filter(
                                    Appointment.location == office_name,
                                    Appointment.office_id == office_id,
                                    Appointment.service_id == service_id,
                                    Appointment.date == appointment_datetime,
                                )
                                .first()
                            )

                            # If it doesn't exist, add it to the database
                            if not existing_appointment:
                                new_appointment = Appointment(
                                    location=office_name,  # Keep location name for reference
                                    office_id=office_id,  # Store office ID
                                    service_id=service_id,  # Store service ID
                                    date=appointment_datetime,
                                )
                                db.add(new_appointment)
                                new_appointments.append(new_appointment)
                                appointments_added += 1

            # Commit after processing all appointments
            if appointments_added > 0:
                db.commit()
                print(
                    f"[{datetime.now()}] Added {appointments_added} new appointments to database"
                )
                notify_subscribers_of_new_appointments(new_appointments)
            else:
                print(f"[{datetime.now()}] No new appointments to add")

            return True

    except Exception as e:
        print(f"[{datetime.now()}] Error syncing appointments to database: {e}")
        return False


def fetch_and_sync_appointments():
    """
    Fetch appointments and sync them to the database
    """
    success = run_appointment_fetcher()
    if success:
        sync_appointments_to_db()


def run_scheduler():
    """
    Set up the scheduler to run the appointment fetch job every minute
    """
    print(f"[{datetime.now()}] Starting appointment scheduler...")

    # Run the job immediately when the script starts
    fetch_and_sync_appointments()

    # Schedule the job to run every minute
    schedule.every(1).minutes.do(fetch_and_sync_appointments)

    # Keep the script running and run pending jobs
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_scheduler()
