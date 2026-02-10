"""Constants for the Mount Alexander Bins integration."""
from datetime import timedelta

DOMAIN = "mount_alexander_bins"

# Config keys
CONF_PROPERTY_ID = "property_id"
CONF_ADDRESS = "address"

# API Configuration — uses the council's own website API
API_BASE_URL = "https://www.mountalexander.vic.gov.au"
API_SEARCH = f"{API_BASE_URL}/api/v1/myarea/search"
API_WASTE_SERVICES = f"{API_BASE_URL}/ocapi/Public/myarea/wasteservices"

# Update interval
SCAN_INTERVAL = timedelta(hours=12)

# Bin types
BIN_GARBAGE = "garbage"
BIN_RECYCLING = "recycling"

BIN_TYPES = {
    BIN_GARBAGE: {
        "name": "General Waste",
        "icon": "mdi:trash-can",
        "color": "red",
    },
    BIN_RECYCLING: {
        "name": "Recycling",
        "icon": "mdi:recycle",
        "color": "yellow",
    },
}

# Mapping from HTML <h3> text to our bin type keys (case-insensitive)
BIN_NAME_MAPPING = {
    "general waste": BIN_GARBAGE,
    "garbage": BIN_GARBAGE,
    "rubbish": BIN_GARBAGE,
    "recycling": BIN_RECYCLING,
    "recycle": BIN_RECYCLING,
}
