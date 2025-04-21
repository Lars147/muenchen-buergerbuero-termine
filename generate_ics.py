#!/usr/bin/env python3
"""
generate_ics_per_category.py

Reads JSON data, then for each top-level category (e.g. "REISEPASS"),
generates a separate ICS calendar file, containing all appointments
in that category.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

from webpush.constants import Office, Services

# ------------
# CONFIG
# ------------
JSON_FILE = "appointments.json"  # Input JSON with the structure shown in the example
OUTPUT_DIR_NAME = "ics"  # Output directory for ICS files
TZ = ZoneInfo("Europe/Berlin")  # Timezone for the appointments


def clean_filename(name):
    """
    Convert category name into a filename-friendly string, e.g. removing spaces, slashes, etc.
    """
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", name)


def load_appointments(json_file):
    """Load the appointment data from the JSON file."""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def generate_ics_for_category(service, appointments):
    """
    Create an ICS Calendar object for a single category.
    appointments is the dict of { location -> { date -> {...} } }
    """
    now = datetime.now().astimezone(TZ)
    service = Services[service]

    cal = Calendar()
    cal.add("prodid", f"-//Appointments Buergerbuero Muenchen//{service.name}//")
    cal.add("version", "2.0")
    cal.add("method", "PUBLISH")
    cal.add("calscale", "GREGORIAN")

    # Iterate over locations in this category
    for office_name, dates_dict in appointments.items():
        office = Office[office_name]
        for date_str, info in dates_dict.items():
            # If there's an errorCode, skip
            if "errorCode" in info:
                continue

            # appointmentTimestamps is the list of start times (epoch)
            timestamps = info.get("appointmentTimestamps", [])
            for start_ts in timestamps:
                start_dt = datetime.fromtimestamp(start_ts, tz=TZ)
                end_dt = start_dt + timedelta(minutes=15)  # Each appointment is 15 min

                event = Event()
                event.add("summary", f"{service.name} - {office_name}")
                event.add("dtstart", start_dt)
                event.add("dtend", end_dt)
                event.add("dtstamp", datetime.now())
                event.add("location", office.address)
                event.add(
                    "description",
                    f"Termin buchen: https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/{service.value}/\n\n"
                    f"Zuletzt abgerufen: {now.strftime('%d.%m.%Y %H:%M:%S %Z (%z)')}\n"
                    f"Zuletzt geupdated (muenchen.de): {datetime.fromtimestamp(int(info['lastModified']) / 1000, tz=TZ).strftime('%d.%m.%Y %H:%M:%S %Z (%z)')}",
                )
                # Unique identifier for the event
                event["uid"] = f"{start_ts}-{office_name.replace(' ', '_')}"

                cal.add_component(event)

    return cal


def main():
    data = load_appointments(JSON_FILE)

    # For each top-level category (key), generate one ICS file
    # Create output directory if it doesn't exist
    output_dir = Path(OUTPUT_DIR_NAME)
    output_dir.mkdir(exist_ok=True)

    for service, appointments in data.items():
        cal = generate_ics_for_category(service, appointments)

        # Make a safe filename from the category name
        safe_cat = clean_filename(service)
        output_file = output_dir / f"{safe_cat}.ics"

        with open(output_file, "wb") as f:
            f.write(cal.to_ical())

        print(f"Created ICS for category '{service}' -> {output_file}")


if __name__ == "__main__":
    main()
