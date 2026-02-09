"""Constants for the Mount Alexander Bins integration."""
from datetime import timedelta

DOMAIN = "mount_alexander_bins"
DEFAULT_NAME = "Mount Alexander Bins"

# API Configuration
API_BASE_URL = "https://mountalexander.waste-info.com.au"
API_AUTOCOMPLETE = f"{API_BASE_URL}/autocomplete.php"
API_GET_DETAILS = f"{API_BASE_URL}/get_details.php"

# Update interval
SCAN_INTERVAL = timedelta(hours=12)

# Bin types with their colors and icons
BIN_TYPES = {
    "garbage": {
        "name": "Garbage",
        "color": "Red",
        "icon": "mdi:trash-can",
    },
    "recycling": {
        "name": "Recycling",
        "color": "Yellow",
        "icon": "mdi:recycle",
    },
    "organics": {
        "name": "Organics",
        "color": "Green",
        "icon": "mdi:leaf",
    },
}