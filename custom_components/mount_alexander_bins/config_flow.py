"""Config flow for Mount Alexander Bins integration.

Two-step flow:
  1. user   — search for address by typing
  2. select — pick from matching addresses (if multiple)
  3. confirm — test connection and create entry
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MountAlexanderBinsAPI
from .const import CONF_ADDRESS, CONF_PROPERTY_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mount Alexander Bins."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._addresses: list[dict] = []
        self._selected_address: dict | None = None

    def _get_api(self) -> MountAlexanderBinsAPI:
        """Get an API client instance."""
        session = async_get_clientsession(self.hass)
        return MountAlexanderBinsAPI(session)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - address search."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api = self._get_api()

            try:
                self._addresses = await api.search_addresses(
                    user_input[CONF_ADDRESS]
                )
            except Exception:
                _LOGGER.exception("Error searching addresses")
                errors["base"] = "cannot_connect"
            else:
                if not self._addresses:
                    errors[CONF_ADDRESS] = "no_results"
                elif len(self._addresses) == 1:
                    self._selected_address = self._addresses[0]
                    return await self.async_step_confirm()
                else:
                    return await self.async_step_select()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address selection when multiple results are found."""
        if user_input is not None:
            selected_id = user_input[CONF_PROPERTY_ID]
            for addr in self._addresses:
                if addr["Id"] == selected_id:
                    self._selected_address = addr
                    break
            return await self.async_step_confirm()

        address_options = {
            addr["Id"]: addr["AddressSingleLine"]
            for addr in self._addresses
        }

        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PROPERTY_ID): vol.In(address_options),
                }
            ),
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the selected address and test the connection."""
        if not self._selected_address:
            return self.async_abort(reason="no_address_selected")

        property_id = self._selected_address["Id"]
        address = self._selected_address["AddressSingleLine"]

        if user_input is not None:
            # Check we don't already have this property configured
            await self.async_set_unique_id(property_id)
            self._abort_if_unique_id_configured()

            # Test the connection
            session = async_get_clientsession(self.hass)
            api = MountAlexanderBinsAPI(session, property_id)

            try:
                result = await api.test_connection()
            except Exception:
                _LOGGER.exception("Error testing connection")
                return self.async_abort(reason="cannot_connect")

            if not result:
                return self.async_abort(reason="no_services")

            return self.async_create_entry(
                title=address,
                data={
                    CONF_PROPERTY_ID: property_id,
                    CONF_ADDRESS: address,
                },
            )

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"address": address},
        )
