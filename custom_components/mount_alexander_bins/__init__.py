"""The Mount Alexander Bins integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MountAlexanderBinsAPI
from .const import CONF_ADDRESS, CONF_PROPERTY_ID, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mount Alexander Bins from a config entry."""
    session = async_get_clientsession(hass)
    api = MountAlexanderBinsAPI(
        session,
        property_id=entry.data[CONF_PROPERTY_ID],
    )
    api.address = entry.data.get(CONF_ADDRESS)

    coordinator = MountAlexanderBinsDataUpdateCoordinator(
        hass,
        api=api,
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
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self):
        """Update data via API."""
        try:
            return await self.api.get_collection_schedule()
        except Exception as err:
            msg = f"Error communicating with API: {err}"
            raise UpdateFailed(msg) from err
