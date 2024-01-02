from __future__ import annotations

import asyncio
from datetime import timedelta
from multiprocessing import AuthenticationError
from aiohttp import ClientError
import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError
from requests.exceptions import HTTPError

import logging

from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.template import Template, attach
from jinja2 import pass_context

from .const import (
    AREA_INFO,
    TZ_INFO,
)


class EntsoeCoordinator(DataUpdateCoordinator):
    """Get the latest data and update the states."""

    def __init__(self, hass: HomeAssistant, api_key, area, timezone) -> None:
        """Initialize the data object."""
        self.hass = hass
        self.api_key = api_key
        self.area = AREA_INFO[area]["code"]
        self.timezone = TZ_INFO[timezone]["timezone"]

        logger = logging.getLogger(__name__)
        super().__init__(
            hass,
            logger,
            name="ENTSO-e coordinator",
            update_interval=timedelta(minutes=60),
        )

    async def _async_update_data(self) -> dict:
        """Get the latest data from ENTSO-e"""
        self.logger.debug("Fetching ENTSO-e data")
        self.logger.debug(f"Bidding zone: {self.area}")
        self.logger.debug(f"Timezone:  {self.timezone}")

        tz = self.timezone

        start_today = pd.Timestamp.now(tz).floor("1D")
        end_today = pd.Timestamp.now(tz).ceil(freq="1D") - pd.Timedelta(seconds=1)
        start_tomorrow = (pd.Timestamp.now(tz) + pd.DateOffset(days=1)).floor("1D")
        end_tomorrow = (pd.Timestamp.now(tz) + pd.DateOffset(days=1)).ceil(
            freq="1D"
        ) - pd.Timedelta(seconds=1)

        data = await self.fetch_prices(start_today, end_tomorrow)

        if data is not None:
            # entsoe-py returns timestamps in server timezone
            # converting the data series to requested tz just in case these differ
            data = data.reindex(data.index.tz_convert(tz))

            # todo: refactor, only handle pandas.Timestamps within this class, since
            # pandas.Timestamp seems generally buggy, HomeAssistant doesn't support it and
            # timestamps anyway converted to string in dict that is put in the extra attributes
            # of the sensor entity.
            # also read https://github.com/EnergieID/entsoe-py/issues/187 and quickfix #202

            # convert all prices (in pd.Series) from €/MWh to €-cent/kWh = divide by 10.0
            data = round(( data / 10.0 ), 3)

            # using .loc[] to slice today and tomorrow
            # .loc[] throws KeyError if missing so we need to catch this silently
            try:
                dataToday = data.loc[start_today.strftime("%Y-%m-%d")].to_dict()
            except KeyError as kerr:
                dataToday = {}
            try:
                # only return a full set of 23 or more items(hours) for 'tomorrow'
                dataTomorrow = (
                    data.loc[start_tomorrow.strftime("%Y-%m-%d")].to_dict()
                    if data.loc[start_tomorrow.strftime("%Y-%m-%d")].size >= 23
                    else {}
                )
            except KeyError as kerr:
                dataTomorrow = {}

            return {
                "data": data.to_dict(),
                "dataToday": dataToday,
                "dataTomorrow": dataTomorrow,
            }
        elif self.data is not None:
            # Note to self: we never come here since fetch_prices already throws if data is None

            return {
                "data": self.data["data"],
                "dataToday": self.data["dataToday"],
                "dataTomorrow": self.data["dataTomorrow"],
            }

    async def fetch_prices(self, start_date, end_date):
        try:
            # run api_update in async job
            resp = await self.hass.async_add_executor_job(
                self.api_update, start_date, end_date, self.api_key
            )

            return resp

        except HTTPError as exc:
            if exc.response.status_code == 401:
                raise UpdateFailed("Unauthorized: Please check your API-key.") from exc
        except Exception as exc:
            if self.data is not None:
                newest_timestamp = pd.Timestamp(list(self.data["data"])[-1])
                if (newest_timestamp) > pd.Timestamp.now(newest_timestamp.tzinfo):
                    self.logger.warning(
                        f"Warning the integration is running in degraded mode (falling back on stored data) since fetching the latest ENTSOE-e prices failed with exception: {exc}."
                    )
                else:
                    self.logger.error(
                        f"Error the latest available data is older than the current time. Therefore entities will no longer update. {exc}"
                    )
                    raise UpdateFailed(
                        f"Unexpected error when fetching ENTSO-e prices: {exc}"
                    ) from exc
            else:
                self.logger.warning(
                    f"Warning the integration doesn't have any up to date local data this means that entities won't get updated but access remains to restorable entities: {exc}."
                )

    def api_update(self, start_date, end_date, api_key):
        client = EntsoePandasClient(api_key=api_key)
        return client.query_day_ahead_prices(
            country_code=self.area, start=start_date, end=end_date
        )

    def processed_data(self):
        return {
            "prices_today": self.get_timestamped_prices(self.data["dataToday"]),
            "prices_tomorrow": self.get_timestamped_prices(self.data["dataTomorrow"]),
            "time_today": self.get_today(),
            "time_tomorrow": self.get_tomorrow(),
        }

    def get_timestamped_prices(self, hourprices):
        list = []
        for hour, price in hourprices.items():
            str_hour = str(hour)
            list.append({"time": str_hour, "price": price})
        return list

    def get_today(self):
        return pd.Timestamp.now(self.timezone).floor("1D").to_pydatetime()

    def get_tomorrow(self):
        return (
            (pd.Timestamp.now(self.timezone) + pd.DateOffset(days=1))
            .floor("1D")
            .to_pydatetime()
        )
