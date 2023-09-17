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


class EntsoeSensor(CoordinatorEntity, RestoreSensor):
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
        self.entity_description: EntsoeEntityDescription = description

        self._update_job = HassJob(self.async_schedule_update_ha_state)
        self._unsub_update = None

        super().__init__(coordinator)

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        _LOGGER.debug(f"Trying to restore last sensor data: check if existing!!")
        # if (last_sensor_data := await self.async_get_last_sensor_data()) is not None:
        #     # new introduced in 2022.04
        #     _LOGGER.debug(f"Trying to restore last sensor data: {last_sensor_data}")
        #     if last_sensor_data.native_value is not None:
        #         self._attr_native_value = last_sensor_data.native_value
        #     if last_sensor_data._attr_extra_state_attributes is not None:
        #         self._attr_extra_state_attributes = dict(
        #             last_sensor_data._attr_extra_state_attributes
        #         )

    async def async_update(self) -> None:
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

            # selected_keys = {"prices_today"}
            # if (
            #     self.description.key == "prices_today"
            #     and self._attr_native_value is not None
            # ):
            #     self._attr_extra_state_attributes = {
            #         x: self.coordinator.processed_data()[x]
            #         for x in self.coordinator.processed_data()
            #         if x in selected_keys
            #     }

            # selected_keys = {"prices_tomorrow"}
            # if (
            #     self.description.key == "prices_tomorrow"
            #     and self._attr_native_value is not None
            # ):
            #     self._attr_extra_state_attributes = {
            #         x: self.coordinator.processed_data()[x]
            #         for x in self.coordinator.processed_data()
            #         if x in selected_keys
            #     }

        # Cancel the currently scheduled event if there is any
        if self._unsub_update:
            self._unsub_update()
            self._unsub_update = None

        # Schedule the next update at exactly the next whole hour sharp
        self._unsub_update = event.async_track_point_in_utc_time(
            self.hass,
            self._update_job,
            utcnow().replace(minute=0, second=0) + timedelta(minutes=5),
        )

    @property
    def extra_restore_state_data(self) -> EntsoeSensorExtraStoredData:
        """Return sensor specific state data to be restored."""
        return EntsoeSensorExtraStoredData(
            self._attr_native_value,
            None,
            self._attr_extra_state_attributes
            if hasattr(self, "_attr_extra_state_attributes")
            else None,
        )

    async def async_get_last_sensor_data(self) -> EntsoeSensorExtraStoredData | None:
        """Restore Entsoe-e Sensor Extra Stored Data."""
        if (restored_last_extra_data := await self.async_get_last_extra_data()) is None:
            return None

        _LOGGER.debug(f"Dict: {restored_last_extra_data.as_dict()}")

        if self.coordinator.data is not None:
            if self.description.key == "prices_today":
                self.coordinator.data[
                    "prices_today"
                ] = restored_last_extra_data.as_dict()["_attr_extra_state_attributes"]

            if self.description.key == "prices_tomorrow":
                self.coordinator.data[
                    "prices_tomorrow"
                ] = restored_last_extra_data.as_dict()["_attr_extra_state_attributes"]

        return EntsoeSensorExtraStoredData.from_dict(restored_last_extra_data.as_dict())
