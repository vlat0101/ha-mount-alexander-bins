"""Config flow for Mount Alexander Bins integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MountAlexanderBinsAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MountAlexanderBinsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mount Alexander Bins."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.address_results: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = MountAlexanderBinsAPI(session)

            try:
                self.address_results = await api.search_address(user_input["address"])

                if not self.address_results:
                    errors["base"] = "no_results"
                elif len(self.address_results) == 1:
                    # Only one result, proceed directly
                    return self.async_create_entry(
                        title=self.address_results[0]["address"],
                        data={
                            "address": self.address_results[0]["address"],
                            "property_id": self.address_results[0]["property_id"],
                        },
                    )
                else:
                    # Multiple results, let user choose
                    return await self.async_step_select_address()

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("address"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle address selection when multiple results are found."""
        if user_input is not None:
            selected_address = user_input["selected_address"]
            
            # Find the selected property
            for result in self.address_results:
                if result["address"] == selected_address:
                    return self.async_create_entry(
                        title=result["address"],
                        data={
                            "address": result["address"],
                            "property_id": result["property_id"],
                        },
                    )

        # Create options for dropdown
        address_options = {
            result["address"]: result["address"] for result in self.address_results
        }

        return self.async_show_form(
            step_id="select_address",
            data_schema=vol.Schema(
                {
                    vol.Required("selected_address"): vol.In(address_options),
                }
            ),
        )