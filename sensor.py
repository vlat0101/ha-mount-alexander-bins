"""Sensor platform for Mount Alexander Bins integration."""
from __future__ import annotations

from datetime import datetime, date
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import BIN_TYPES, CONF_ADDRESS, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    address = entry.data.get(CONF_ADDRESS, "Unknown")

    entities = []

    # Create a sensor for each bin type that appears in the data
    # Also create sensors for standard types even if not yet in data
    known_types = set(BIN_TYPES.keys())
    if coordinator.data:
        known_types.update(coordinator.data.keys())

    for bin_key in known_types:
        bin_info = BIN_TYPES.get(bin_key, {
            "name": bin_key.replace("_", " ").title(),
            "icon": "mdi:trash-can",
            "color": "unknown",
        })
        entities.append(
            BinCollectionSensor(coordinator, entry, bin_key, bin_info, address)
        )

    # Add a "next bin" summary sensor
    entities.append(NextBinSensor(coordinator, entry, address))

    async_add_entities(entities)


class BinCollectionSensor(CoordinatorEntity, SensorEntity):
    """Sensor for an individual bin type."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        bin_key: str,
        bin_info: dict,
        address: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._bin_key = bin_key
        self._bin_info = bin_info
        self._attr_unique_id = f"{entry.entry_id}_{bin_key}"
        self._attr_name = f"{bin_info['name']} Bin"
        self._attr_icon = bin_info["icon"]

    @property
    def native_value(self) -> str | None:
        """Return the next collection date."""
        if self.coordinator.data and self._bin_key in self.coordinator.data:
            return self.coordinator.data[self._bin_key]
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        attrs = {
            "bin_color": self._bin_info.get("color", "unknown"),
            "bin_type": self._bin_info.get("name", self._bin_key),
        }

        collection_date = self.native_value
        if collection_date:
            try:
                dt = datetime.strptime(collection_date, "%Y-%m-%d").date()
                today = date.today()
                days_until = (dt - today).days
                attrs["days_until_collection"] = days_until

                if days_until == 0:
                    attrs["collection_status"] = "today"
                elif days_until == 1:
                    attrs["collection_status"] = "tomorrow"
                elif days_until < 0:
                    attrs["collection_status"] = "overdue"
                else:
                    attrs["collection_status"] = f"in {days_until} days"
            except ValueError:
                pass

        return attrs


class NextBinSensor(CoordinatorEntity, SensorEntity):
    """Sensor that shows which bin is collected next."""

    _attr_has_entity_name = True
    _attr_name = "Next Bin Collection"
    _attr_icon = "mdi:delete-empty"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        address: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_next_bin"

    @property
    def native_value(self) -> str | None:
        """Return the next bin type to be collected."""
        if not self.coordinator.data:
            return None

        today = date.today()
        next_bin = None
        next_date = None

        for bin_key, date_str in self.coordinator.data.items():
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d").date()
                if dt >= today and (next_date is None or dt < next_date):
                    next_date = dt
                    next_bin = bin_key
            except ValueError:
                continue

        if next_bin and next_bin in BIN_TYPES:
            return BIN_TYPES[next_bin]["name"]
        elif next_bin:
            return next_bin.replace("_", " ").title()
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}

        today = date.today()
        next_bin = None
        next_date = None

        for bin_key, date_str in self.coordinator.data.items():
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d").date()
                if dt >= today and (next_date is None or dt < next_date):
                    next_date = dt
                    next_bin = bin_key
            except ValueError:
                continue

        attrs = {}
        if next_date:
            days_until = (next_date - today).days
            attrs["next_collection_date"] = next_date.isoformat()
            attrs["days_until_collection"] = days_until

            if days_until == 0:
                attrs["collection_status"] = "today"
            elif days_until == 1:
                attrs["collection_status"] = "tomorrow"
            else:
                attrs["collection_status"] = f"in {days_until} days"

        if next_bin and next_bin in BIN_TYPES:
            attrs["bin_color"] = BIN_TYPES[next_bin]["color"]

        # List all upcoming collections
        all_upcoming = {}
        for bin_key, date_str in self.coordinator.data.items():
            name = BIN_TYPES.get(bin_key, {}).get("name", bin_key.replace("_", " ").title())
            all_upcoming[name] = date_str
        if all_upcoming:
            attrs["all_upcoming"] = all_upcoming

        return attrs
