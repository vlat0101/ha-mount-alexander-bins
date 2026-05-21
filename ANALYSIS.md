# ha-mount-alexander-bins

## Project Name & Summary
**Name:** ha-mount-alexander-bins  
**Status:** Published  
**Purpose:** Home Assistant custom component for Mount Alexander Shire bin collection integration

## Purpose & Scope (Operational)
- **Type:** Home Assistant Custom Component (HACS)
- **Function:** Provides bin collection day information for Mount Alexander Shire residents
- **Status:** ✅ Published - Available on HACS
- **Distribution:** Home Assistant Community Store (HACS)

## Tech Stack & Dependencies (Operational)
- **Python** - HA custom component
- **Home Assistant** - Core platform
- **YAML** - Configuration

## Key Files & Directory Structure (Technical)
```
ha-mount-alexander-bins/
├── HACS.json                          # HACS manifest file
├── INFO.md                            # HACS information page
├── README.md                          # Project documentation
├── custom_components/                 # HA custom component structure
│   └── mount_alexander_bins/         # Component folder
│       ├── __init__.py               # Component initialization
│       ├── config_flow.py            # Config flow handler
│       ├── const.py                  # Constants
│       ├── coordinator.py            # Data update coordinator
│       ├── binary_sensor.py          # Binary sensor platform
│       └── manifest.json             # Component manifest
├── .gitignore                         # Git ignore rules
└── CONTRIBUTING.md                    # Contribution guidelines
```

## Code Structure Overview (Technical)
- **Component Type:** Home Assistant custom component
- **Integration Pattern:** Uses HA's `custom_component` structure
- **Data Source:** Mount Alexander Shire bin collection schedule
- **Platform:** Binary sensor for bin collection status
- **Config Flow:** User-friendly configuration via HA UI

## API Endpoints/Interfaces (Technical)
- **Home Assistant API:** Binary sensor platform for bin status
- **Configuration:** YAML or UI-based configuration
- **Webhook Support:** Possibly for external data updates

## Current Status & Development State
- **Status:** ✅ Published - Production deployment
- **Distribution:** Available via HACS
- **Maintenance:** Active maintenance with contribution guidelines

## Cross-References to Related Projects
- **Integrates with:** `../HassIO/` (Home Assistant)
- **Related:** `../ha-smart-bin-reminder/` (user-facing package)
- **Related:** `../ha-bin-check/` (bin check automation)
- **Related:** `../bin-monitor/` (camera-based monitoring)
- **Supersedes:** `../_archive/mount_alexander_bins/` (old version)