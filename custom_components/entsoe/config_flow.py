"""Config flow for Forecast.Solar integration."""
from __future__ import annotations

from typing import Any
import re

import voluptuous as vol

import logging

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelectorConfig,
    SelectSelector,
    SelectOptionDict,
    TemplateSelectorConfig,
    TemplateSelector,
)
from homeassistant.helpers.template import Template

from .const import (
    CONF_API_KEY,
    CONF_ENTITY_NAME,
    CONF_AREA,
    DOMAIN,
    COMPONENT_TITLE,
    UNIQUE_ID,
    AREA_INFO,
)


class EntsoeFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Entsoe."""

    def __init__(self):
        """Initialize ENTSO-e ConfigFlow."""
        self.area = None
        # self.advanced_options = None
        self.api_key = None
        # self.modifyer = None
        self.name = ""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> EntsoeOptionFlowHandler:
        """Get the options flow for this handler."""
        return EntsoeOptionFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        errors = {}
        already_configured = False

        if user_input is not None:
            self.area = user_input[CONF_AREA]
            self.api_key = user_input[CONF_API_KEY]
            self.name = user_input[CONF_ENTITY_NAME]

            if user_input[CONF_ENTITY_NAME] not in (None, ""):
                self.name = user_input[CONF_ENTITY_NAME]
            NAMED_UNIQUE_ID = self.name + UNIQUE_ID
            try:
                await self.async_set_unique_id(NAMED_UNIQUE_ID)
                self._abort_if_unique_id_configured()
            except Exception as e:
                errors["base"] = "already_configured"
                already_configured = True

            if not already_configured:
                return self.async_create_entry(
                    title=self.name,
                    data={},
                    options={
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_AREA: user_input[CONF_AREA],
                        CONF_ENTITY_NAME: user_input[CONF_ENTITY_NAME],
                    },
                )

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_ENTITY_NAME, default=""): vol.All(vol.Coerce(str)),
                    vol.Required(CONF_API_KEY): vol.All(vol.Coerce(str)),
                    vol.Required(CONF_AREA): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=country, label=info["name"])
                                for country, info in AREA_INFO.items()
                            ]
                        ),
                    ),
                },
            ),
        )

