"""Sensor platform for Mount Alexander Bins integration."""
from datetime import date, datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MountAlexanderBinsDataUpdateCoordinator
from .const import BIN_TYPES, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mount Alexander Bins sensors."""
    coordinator: MountAlexanderBinsDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities = []

    # Add individual bin sensors for each available bin type
    for bin_type in coordinator.data:
        entities.append(MountAlexanderBinSensor(coordinator, entry, bin_type))

    # Add a "next collection" sensor
    entities.append(NextCollectionSensor(coordinator, entry))

    async_add_entities(entities)


class MountAlexanderBinSensor(CoordinatorEntity, SensorEntity):
    """Representation of a bin collection sensor."""

    def __init__(
        self,
        coordinator: MountAlexanderBinsDataUpdateCoordinator,
        entry: ConfigEntry,
        bin_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.bin_type = bin_type
        self._attr_unique_id = f"{entry.entry_id}_{bin_type}"
        self._attr_name = f"{BIN_TYPES[bin_type]['name']} Bin"
        self._attr_icon = BIN_TYPES[bin_type]["icon"]

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        if self.bin_type not in self.coordinator.data:
            return None

        next_collection = self.coordinator.data[self.bin_type]["next_collection"]
        return next_collection.strftime("%A, %d %B %Y")

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if self.bin_type not in self.coordinator.data:
            return {}

        next_collection = self.coordinator.data[self.bin_type]["next_collection"]
        today = date.today()
        days_until = (next_collection - today).days

        # Determine urgency level
        if days_until == 0:
            urgency = "critical"
            reminder = "Collection is TODAY!"
        elif days_until == 1:
            urgency = "high"
            reminder = "Collection is TOMORROW!"
        elif days_until <= 3:
            urgency = "normal"
            reminder = f"Collection in {days_until} days"
        else:
            urgency = "low"
            reminder = f"Collection in {days_until} days"

        return {
            "days_until": days_until,
            "urgency": urgency,
            "reminder": reminder,
            "next_collection_date": next_collection.isoformat(),
            "bin_color": BIN_TYPES[self.bin_type]["color"],
        }


class NextCollectionSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the next bin collection (any bin type)."""

    def __init__(
        self,
        coordinator: MountAlexanderBinsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_next_collection"
        self._attr_name = "Next Bin Collection"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        # Find the soonest collection date
        next_date = None
        for bin_data in self.coordinator.data.values():
            collection_date = bin_data["next_collection"]
            if next_date is None or collection_date < next_date:
                next_date = collection_date

        if next_date:
            return next_date.strftime("%A, %d %B %Y")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {}

        # Find the soonest collection date and which bins
        next_date = None
        bins_due = []

        for bin_type, bin_data in self.coordinator.data.items():
            collection_date = bin_data["next_collection"]
            if next_date is None or collection_date < next_date:
                next_date = collection_date
                bins_due = [bin_type]
            elif collection_date == next_date:
                bins_due.append(bin_type)

        if not next_date:
            return {}

        today = date.today()
        days_until = (next_date - today).days

        # Determine urgency level
        if days_until == 0:
            urgency = "critical"
            reminder = "Collection is TODAY!"
        elif days_until == 1:
            urgency = "high"
            reminder = "Collection is TOMORROW!"
        elif days_until <= 3:
            urgency = "normal"
            reminder = f"Collection in {days_until} days"
        else:
            urgency = "low"
            reminder = f"Collection in {days_until} days"

        # Build bin names list
        bin_names = [BIN_TYPES[bt]["name"] for bt in bins_due if bt in BIN_TYPES]

        return {
            "bins": bins_due,
            "bin_names": ", ".join(bin_names),
            "days_until": days_until,
            "urgency": urgency,
            "reminder": reminder,
            "next_collection_date": next_date.isoformat(),
        }
``