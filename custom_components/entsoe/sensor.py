"""ENTSO-e current electricity and gas price information service."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import pandas as pd

from homeassistant.components.sensor import (
    DOMAIN,
    # SensorStateClass,
    SensorDeviceClass,
    RestoreSensor,
    SensorExtraStoredData,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HassJob, HomeAssistant
from homeassistant.helpers import event
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import utcnow
from .const import (
    ATTRIBUTION,
    CONF_COORDINATOR,
    CONF_ENTITY_NAME,
    DOMAIN,
    EntsoeEntityDescription,
    ICON,
    SENSOR_TYPES,
)
from .coordinator import EntsoeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ENTSO-e price sensor entries."""
    entsoe_coordinator = hass.data[DOMAIN][config_entry.entry_id][CONF_COORDINATOR]

    entities = []
    entity = {}
    for description in SENSOR_TYPES:
        entity = description
        entities.append(
            EntsoeSensor(
                entsoe_coordinator, entity, config_entry.options[CONF_ENTITY_NAME]
            )
        )

    # Add an entity for each sensor type
    async_add_entities(entities, True)


class EntsoeSensorExtraStoredData(SensorExtraStoredData):
    """Object to hold extra stored data."""

    _attr_extra_state_attributes: any

    def __init__(
        self, native_value, native_unit_of_measurement, _attr_extra_state_attributes
    ) -> None:
        super().__init__(native_value, native_unit_of_measurement)
        self._attr_extra_state_attributes = _attr_extra_state_attributes

    def as_dict(self) -> dict[str, any]:
        """Return a dict representation of the utility sensor data."""
        data = super().as_dict()
        data["_attr_extra_state_attributes"] = (
            self._attr_extra_state_attributes
            if self._attr_extra_state_attributes is not None
            else None
        )

        return data

    @classmethod
    def from_dict(cls, restored: dict[str, Any]) -> EntsoeSensorExtraStoredData | None:
        """Initialize a stored sensor state from a dict."""
        extra = SensorExtraStoredData.from_dict(restored)
        if extra is None:
            return None

        _attr_extra_state_attributes: any = (
            restored["_attr_extra_state_attributes"]
            if "_attr_extra_state_attributes" in restored
            else None
        )

        return cls(
            extra.native_value,
            extra.native_unit_of_measurement,
            _attr_extra_state_attributes,
        )


class EntsoeSensor(CoordinatorEntity):
    """Representation of a ENTSO-e sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_icon = ICON
    # _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: EntsoeCoordinator,
        description: EntsoeEntityDescription,
        name: str = "",
    ) -> None:
        """Initialize the sensor."""
        self.description = description

        if name not in (None, ""):
            # The Id used for addressing the entity in the ui, recorder history etc.
            self.entity_id = f"{DOMAIN}.{name}_{description.key}"
            # unique id in .storage file for ui configuration.
            self._attr_unique_id = f"entsoe.{name}_{description.key}"
            self._attr_name = f"[ENTSO-e] {description.name} ({name})"
        else:
            self.entity_id = f"{DOMAIN}.entsoe_{description.key}"
            self._attr_unique_id = f"entsoe.{description.key}"
            self._attr_name = f"[ENTSO-e] {description.name}"

        self._attr_device_class = (
            SensorDeviceClass.MONETARY
            if description.device_class is None
            else description.device_class
        )
        self._attr_state_class = None if self._attr_device_class in [SensorDeviceClass.TIMESTAMP, SensorDeviceClass.MONETARY] else SensorStateClass.MEASUREMENT
        self.entity_description: EntsoeEntityDescription = description

        self._update_job = HassJob(self.async_schedule_update_ha_state)
        self._unsub_update = None

        super().__init__(coordinator)

    async def async_update(self) -> None:
        _LOGGER.debug(f"async_update")
        """Get the latest data and updates the states."""
        value: Any = None
        if self.coordinator.data is not None:
            try:
                self._attr_native_value = self.entity_description.value_fn(
                    self.coordinator.processed_data()
                )
            except Exception as exc:
                # No data available
                _LOGGER.warning(
                    f"Unable to update entity due to data processing error: {value} and error: {exc}"
                )

            selected_keys = {"prices_today", "prices_tomorrow"}
            for x in selected_keys:
                if self.description.key == x and self._attr_native_value is not None:
                    self._attr_extra_state_attributes = {
                        x: self.coordinator.processed_data()[x]
                    }

        # Cancel the currently scheduled event if there is any
        if self._unsub_update:
            self._unsub_update()
            self._unsub_update = None

        # Schedule the next update at exactly the next whole hour sharp
        self._unsub_update = event.async_track_point_in_utc_time(
            self.hass,
            self._update_job,
            utcnow().replace(minute=0, second=0) + timedelta(minutes=60),
        )

