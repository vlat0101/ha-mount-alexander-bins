"""The Mount Alexander Bins integration."""
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MountAlexanderBinsAPI
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mount Alexander Bins from a config entry."""
    session = async_get_clientsession(hass)
    api = MountAlexanderBinsAPI(session)

    coordinator = MountAlexanderBinsDataUpdateCoordinator(
        hass,
        api=api,
        property_id=entry.data["property_id"],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class MountAlexanderBinsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching bin collection data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MountAlexanderBinsAPI,
        property_id: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self.property_id = property_id

    async def _async_update_data(self):
        """Update data via API."""
        try:
            return await self.api.get_collection_details(self.property_id)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err