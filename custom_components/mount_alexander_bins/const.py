"""Constants for the Mount Alexander Bins integration."""
from datetime import timedelta

DOMAIN = "mount_alexander_bins"
DEFAULT_NAME = "Mount Alexander Bins"

# API Configuration
API_BASE_URL = "https://www.mountalexander.vic.gov.au"
API_ADDRESS_SEARCH = f"{API_BASE_URL}/api/v1/myarea/searchfuzzy"
API_WASTE_SERVICES = f"{API_BASE_URL}/ocapi/Public/myarea/wasteservices"

# Update interval
SCAN_INTERVAL = timedelta(hours=12)

# Bin types with their colors and icons
# Note: Mount Alexander Shire only has General Waste and Recycling (no organics)
BIN_TYPES = {
    "garbage": {
        "name": "General Waste",
        "color": "Red",
        "icon": "mdi:trash-can",
        "html_class": "general-waste",
    },
    "recycling": {
        "name": "Recycling",
        "color": "Yellow",
        "icon": "mdi:recycle",
        "html_class": "recycling",
    },
}
