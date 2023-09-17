from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    CURRENCY_EURO,
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
)
from homeassistant.helpers.typing import StateType

ATTRIBUTION = "Data provided by ENTSO-e Transparency Platform"
DOMAIN = "entsoe"
ICON = "mdi:currency-eur"
UNIQUE_ID = f"{DOMAIN}_component"
COMPONENT_TITLE = "ENTSO-e Transparency Platform - Day-ahead Prices"

CONF_API_KEY = "api_key"
CONF_ENTITY_NAME = "name"
CONF_AREA = "area"
CONF_TZ = "timezone"
CONF_COORDINATOR = "coordinator"

# Commented ones are not working at entsoe
AREA_INFO = {
    "FI": {"code": "FI", "name": "Finland", "Currency": "EUR"},
    "AT": {"code": "AT", "name": "Austria", "Currency": "EUR"},
    "BE": {"code": "BE", "name": "Belgium", "Currency": "EUR"},
    "BG": {"code": "BG", "name": "Bulgaria", "Currency": "EUR"},
    "HR": {"code": "HR", "name": "Croatia", "Currency": "EUR"},
    "CZ": {"code": "CZ", "name": "Czech Republic", "Currency": "EUR"},
    "DK_1": {"code": "DK_1", "name": "Denmark Western (DK1)", "Currency": "EUR"},
    "DK_2": {"code": "DK_2", "name": "Denmark Eastern (DK2)", "Currency": "EUR"},
    "EE": {"code": "EE", "name": "Estonia", "Currency": "EUR"},
    "FR": {"code": "FR", "name": "France", "Currency": "EUR"},
    "DE": {"code": "DE_LU", "name": "Germany", "Currency": "EUR"},
    "GR": {"code": "GR", "name": "Greece", "Currency": "EUR"},
    "HU": {"code": "HU", "name": "Hungary", "Currency": "EUR"},
    "IT_CNOR": {"code": "IT_CNOR", "name": "Italy Centre North", "Currency": "EUR"},
    "IT_CSUD": {"code": "IT_CSUD", "name": "Italy Centre South", "Currency": "EUR"},
    "IT_NORD": {"code": "IT_NORD", "name": "Italy North", "Currency": "EUR"},
    "IT_SUD": {"code": "IT_SUD", "name": "Italy South", "Currency": "EUR"},
    "IT_SICI": {"code": "IT_SICI", "name": "Italy Sicilia", "Currency": "EUR"},
    "IT_SARD": {"code": "IT_SARD", "name": "Italy Sardinia", "Currency": "EUR"},
    "IT_CALA": {"code": "IT_CALA", "name": "Italy Calabria", "Currency": "EUR"},
    "LV": {"code": "LV", "name": "Latvia", "Currency": "EUR"},
    "LT": {"code": "LT", "name": "Lithuania", "Currency": "EUR"},
    "LU": {"code": "DE_LU", "name": "Luxembourg", "Currency": "EUR"},
    "NL": {"code": "NL", "name": "Netherlands", "Currency": "EUR"},
    "NO_1": {"code": "NO_1", "name": "Norway Oslo (NO1)", "Currency": "EUR"},
    "NO_2": {"code": "NO_2", "name": "Norway Kr.Sand (NO2)", "Currency": "EUR"},
    "NO_3": {"code": "NO_3", "name": "Norway Tr.heim (NO3)", "Currency": "EUR"},
    "NO_4": {"code": "NO_4", "name": "Norway Tromsø (NO4)", "Currency": "EUR"},
    "NO_5": {"code": "NO_5", "name": "Norway Bergen (NO5)", "Currency": "EUR"},
    "PL": {"code": "PL", "name": "Poland", "Currency": "EUR"},
    "PT": {"code": "PT", "name": "Portugal", "Currency": "EUR"},
    "RO": {"code": "RO", "name": "Romania", "Currency": "EUR"},
    "RS": {"code": "RS", "name": "Serbia", "Currency": "EUR"},
    "SK": {"code": "SK", "name": "Slovakia", "Currency": "EUR"},
    "SI": {"code": "SI", "name": "Slovenia", "Currency": "EUR"},
    "ES": {"code": "ES", "name": "Spain", "Currency": "EUR"},
    "SE_1": {"code": "SE_1", "name": "Sweden Luleå (SE1)", "Currency": "EUR"},
    "SE_2": {"code": "SE_2", "name": "Sweden Sundsvall (SE2)", "Currency": "EUR"},
    "SE_3": {"code": "SE_3", "name": "Sweden Stockholm (SE3)", "Currency": "EUR"},
    "SE_4": {"code": "SE_4", "name": "Sweden Malmö (SE4)", "Currency": "EUR"},
    "CH": {"code": "CH", "name": "Switzerland", "Currency": "EUR"},
    #  "UK":{"code":"UK", "name":"United Kingdom", "Currency":"EUR"},
    #  "AL":{"code":"AL", "name":"Albania", "Currency":"EUR"},
    #  "BA":{"code":"BA", "name":"Bosnia and Herz.", "Currency":"EUR"},
    #  "CY":{"code":"CY", "name":"Cyprus", "Currency":"EUR"},
    #  "GE":{"code":"GE", "name":"Georgia", "Currency":"EUR"},
    #  "IE":{"code":"IE", "name":"Ireland", "Currency":"EUR"},
    #  "XK":{"code":"XK", "name":"Kosovo", "Currency":"EUR"},
    #  "MT":{"code":"MT", "name":"Malta", "Currency":"EUR"},
    #  "MD":{"code":"MD", "name":"Moldova", "Currency":"EUR"},
    #  "ME":{"code":"ME", "name":"Montenegro", "Currency":"EUR"},
    #  "MK":{"code":"MK", "name":"North Macedonia", "Currency":"EUR"},
    #  "TR":{"code":"TR", "name":"Turkey", "Currency":"EUR"},
    #  "UA":{"code":"UA", "name":"Ukraine", "Currency":"EUR"},
}

TZ_INFO = {
    "FI": {"code": "FI", "timezone": "Europe/Helsinki"},
    "AT": {"code": "AT", "timezone": "Europe/Vienna"},
    "BE": {"code": "BE", "timezone": "Europe/Brussels"},
    "BG": {"code": "BG", "timezone": "Europe/Sofia"},
    "HR": {"code": "HR", "timezone": "Europe/Zagreb"},
    "CZ": {"code": "CZ", "timezone": "Europe/Prague"},
    "DK": {"code": "DK", "timezone": "Europe/Copenhagen"},
    "EE": {"code": "EE", "timezone": "Europe/Tallinn"},
    "FR": {"code": "FR", "timezone": "Europe/Paris"},
    "DE": {"code": "DE", "timezone": "Europe/Berlin"},
    "GR": {"code": "GR", "timezone": "Europe/Athens"},
    "HU": {"code": "HU", "timezone": "Europe/Budapest"},
    "IT": {"code": "IT", "timezone": "Europe/Rome"},
    "LV": {"code": "LV", "timezone": "Europe/Riga"},
    "LT": {"code": "LT", "timezone": "Europe/Vilnius"},
    "LU": {"code": "LU", "timezone": "Europe/Luxembourg"},
    "NL": {"code": "NL", "timezone": "Europe/Amsterdam"},
    "NO": {"code": "NO", "timezone": "Europe/Oslo"},
    "PL": {"code": "PL", "timezone": "Europe/Warsaw"},
    "PT": {"code": "PT", "timezone": "Europe/Lisbon"},
    "RO": {"code": "RO", "timezone": "Europe/Bucharest"},
    "RS": {"code": "RS", "timezone": "Europe/Belgrade"},
    "SK": {"code": "SK", "timezone": "Europe/Bratislava"},
    "SI": {"code": "SI", "timezone": "Europe/Ljubljana"},
    "ES": {"code": "ES", "timezone": "Europe/Madrid"},
    "SE": {"code": "SE", "timezone": "Europe/Stockholm"},
    "CH": {"code": "CH", "timezone": "Europe/Zurich"},
}


@dataclass
class EntsoeEntityDescription(SensorEntityDescription):
    """Describes ENTSO-e sensor entity."""

    value_fn: Callable[[dict], StateType] = None


SENSOR_TYPES: tuple[EntsoeEntityDescription, ...] = (
    EntsoeEntityDescription(
        key="prices_today",
        name="Prices Today",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data["time_today"],
    ),
    EntsoeEntityDescription(
        key="prices_tomorrow",
        name="Prices Tomorrow",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data["time_tomorrow"],
    ),
)
