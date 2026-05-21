# Mount Alexander Bins - Home Assistant Integration

A custom Home Assistant integration for tracking bin collection schedules for Mount Alexander Shire Council, Victoria, Australia.

## Features

- 🗑️ Track Garbage (Red) and Recycling (Yellow) bin collections
- 📅 Automatic updates twice daily
- 🔔 Rich attributes for automations (days until collection, urgency levels)
- 🎨 Easy configuration through Home Assistant UI
- 📍 Address search with autocomplete

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://git.zxc.com.au/vlat/ha-mount-alexander-bins`
5. Select category "Integration"
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/mount_alexander_bins` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Mount Alexander Bins"
4. Enter your property address (e.g., "123 Main St Castlemaine")
5. Select your address if multiple results appear
6. Done! Your sensors will appear automatically

## Sensors

The integration creates the following sensors:

### Next Bin Collection
- **Entity ID**: `sensor.next_bin_collection`
- **State**: Date of next collection (any bin type)
- **Attributes**:
  - `bins`: List of bin types due
  - `bin_names`: Human-readable bin names
  - `days_until`: Days until collection
  - `urgency`: critical/high/normal/low
  - `reminder`: Text reminder

### Individual Bin Sensors
- **Garbage Bin**: `sensor.garbage_bin`
- **Recycling Bin**: `sensor.recycling_bin`

Each includes:
- Next collection date
- Days until collection
- Urgency level
- Bin color

## Example Automations

### Daily Reminder at 7 PM
```yaml
alias: Bin Night Reminder
trigger:
  - platform: time
    at: "19:00:00"
condition:
  - condition: state
    entity_id: sensor.next_bin_collection
    attribute: days_until
    state: "1"
action:
  - service: notify.mobile_app
    data:
      title: "Bin Night Tomorrow!"
      message: "Put out: {{ state_attr('sensor.next_bin_collection', 'bin_names') }}"
```

### Smart Light Notification
```yaml
alias: Bin Night Light Reminder
trigger:
  - platform: state
    entity_id: sensor.next_bin_collection
    attribute: urgency
    to: "high"
action:
  - service: light.turn_on
    target:
      entity_id: light.hallway
    data:
      color_name: yellow
      brightness: 255
```

## Dashboard Card
```yaml
type: entities
title: Bin Collections
entities:
  - entity: sensor.next_bin_collection
    secondary_info: attribute
    attribute: reminder
  - entity: sensor.garbage_bin
    secondary_info: attribute
    attribute: reminder
  - entity: sensor.recycling_bin
    secondary_info: attribute
    attribute: reminder
```

## Support

For issues, feature requests, or questions, please [open an issue](https://git.zxc.com.au/vlat/ha-mount-alexander-bins/issues).

## License

MIT License
