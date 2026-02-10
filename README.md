# Mount Alexander Bins

A [Home Assistant](https://www.home-assistant.io/) custom integration that tracks bin collection dates for properties in the [Mount Alexander Shire Council](https://www.mountalexander.vic.gov.au/) area (Castlemaine, Harcourt, Newstead, Maldon, etc.).

## Features

- Sensors for each bin type with next collection date
- **General Waste** (red lid) — collected weekly
- **Recycling** (yellow lid) — collected fortnightly
- "Next Bin Collection" summary sensor showing which bin is due next
- Extra attributes: `days_until_collection`, `collection_status` (today/tomorrow/in X days), `bin_color`
- Updates every 12 hours

## Installation

### HACS (Manual Repository)

1. Open HACS in Home Assistant
2. Click the three dots menu (top right) → **Custom repositories**
3. Add `https://github.com/vlat0101/ha-mount-alexander-bins` with category **Integration**
4. Search for "Mount Alexander Bins" and install
5. Restart Home Assistant

### Manual Installation

1. Copy the `mount_alexander_bins` folder to your `custom_components` directory:
   ```
   custom_components/
   └── mount_alexander_bins/
       ├── __init__.py
       ├── api.py
       ├── config_flow.py
       ├── const.py
       ├── manifest.json
       ├── sensor.py
       ├── strings.json
       └── translations/
           └── en.json
   ```
2. Restart Home Assistant

## Setup

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Mount Alexander Bins**
3. Enter your street address (e.g. "120 Barker St Castlemaine")
4. Select your address from the results
5. Confirm to create the sensors

## Sensors Created

| Sensor | Example Value | Description |
|--------|--------------|-------------|
| `sensor.general_waste_bin` | `2026-02-11` | Next general waste collection date |
| `sensor.recycling_bin` | `2026-02-11` | Next recycling collection date |
| `sensor.next_bin_collection` | `General Waste` | Which bin type is collected next |

### Sensor Attributes

Each bin sensor includes:
- `bin_color` — red or yellow
- `bin_type` — General Waste or Recycling
- `days_until_collection` — integer
- `collection_status` — "today", "tomorrow", "in X days", or "overdue"

The "Next Bin Collection" sensor also includes:
- `next_collection_date` — ISO date of the next collection
- `all_upcoming` — dict of all bin types and their next dates

## How It Works

This integration queries the Mount Alexander Shire Council website directly:

1. **Address search** — `/api/v1/myarea/search?keywords=...` returns matching addresses
2. **Waste services** — `/ocapi/Public/myarea/wasteservices?geolocationid=...` returns collection dates as HTML, which is parsed using BeautifulSoup

Data is refreshed every 12 hours.

## Automation Examples

### Bin night reminder (notification at 6pm the day before)

```yaml
automation:
  - alias: "Bin Night Reminder"
    trigger:
      - platform: time
        at: "18:00:00"
    condition:
      - condition: state
        entity_id: sensor.next_bin_collection
        attribute: days_until_collection
        state: 1
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Bin Night!"
          message: >
            Put out the {{ states('sensor.next_bin_collection') }} bin
            — collection is tomorrow.
```

## Requirements

- Home Assistant 2024.1 or newer
- BeautifulSoup4 (installed automatically)

## License

MIT
