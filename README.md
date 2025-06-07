# ⚠️ SERVICE TEMPORARILY UNAVAILABLE

## Rate Limiting Issue
The external service has introduced rate limiting, making the automated GitHub Actions workflow unsustainable. **Automatic updates are currently disabled.**

## Upcoming Server Migration
An upcoming release will migrate this project to a dedicated server to resolve the rate limiting issues and restore automatic updates.

---

# München Bürgerbüro Termine
A repo for gathering available appointment dates and times from [Munich's Bürgerbüros](https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/1063453).

## Available Service Calendars
Every service has its own calendar. All service calendars can be found [here](https://github.com/Lars147/muenchen-buergerbuero-termine/tree/main/ics).

When copying the ICS URL, make sure to copy the **raw** subdomain, e.g. instead of

```
https://github.com/Lars147/muenchen-buergerbuero-termine/blob/main/ics/REISEPASS.ics
```
use
```
https://raw.githubusercontent.com/Lars147/muenchen-buergerbuero-termine/refs/heads/main/ics/REISEPASS.ics
```

## Subscribe to Calendar Updates
You can subscribe to the appointment calendars in your preferred calendar application:

### Apple Calendar (iOS/macOS)
1. Open Calendar app
2. File > New Calendar Subscription
3. Enter the ICS URL
4. Choose refresh frequency and other options
5. Click Subscribe

### Google Calendar
[Random update frequency!](https://gist.github.com/gene1wood/02ed0d36f62d791518e452f55344240d)
1. Open Google Calendar
2. Click the + next to "Other calendars"
3. Select "From URL"
4. Enter the ICS URL
5. Click "Add calendar"

### Microsoft Outlook
1. Open Outlook
2. File > Account Settings > Internet Calendars > New
3. Enter the ICS URL
4. Click "Add"
5. Name your calendar and click OK

### Other Calendar Apps
Most calendar applications support ICS/iCal subscription via URL. Look for options like:
- "Subscribe to calendar"
- "Add calendar from URL"
- "New subscription"

Note: The calendar will automatically update based on your calendar app's refresh settings.

## Details
### Scraping Interval
~~Currently, the Github Action is triggered to run every 10 minutes. This means that the ICS files are updated every 10 minutes.~~

**Update: Automatic scraping is temporarily disabled due to rate limiting. The workflow now requires manual triggering only.**

### JSON File
If you want to consume the information in a different format, you can use the raw [JSON file](appointments.json). It is used to generate the ICS files and is updated every time the script is run.

## Scrap the Data Yourself
1. Install dependencies `pip install -r requirements.txt`
2. Run the Python script: `python get_buergerbuero_appointments.py`
3. Generate the ICS file: `python generate_ics.py`

## TODOs:
- [x] Change calendar names
- [x] Change timezone
- [x] Make appointments more readable (location, last updated, etc.)
- [] Get all service codes (https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/serv)
