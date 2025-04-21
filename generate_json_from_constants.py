import json

from webpush.constants import Office, Services

# Convert Office enum to dictionary
offices = {
    office.name: {
        "verbose_name": office.verbose_name,
        "office_id": office.office_id,
        "address": office.address,
    }
    for office in Office
}

# Convert Services enum to dictionary
services = {service.name: service.value for service in Services}

# Combine both into one dictionary
data = {"offices": offices, "services": services}

# Write to JSON file
with open("constants.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
