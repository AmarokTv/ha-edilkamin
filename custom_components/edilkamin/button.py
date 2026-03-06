"""Platform for button integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add button for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN]["coordinator"]

    async_add_devices(
        [
            EdilkaminRefreshButton(coordinator),
        ]
    )


class EdilkaminRefreshButton(CoordinatorEntity, ButtonEntity):
    """Representation of a Refresh Button."""

    def __init__(self, coordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._mac_address = self.coordinator.get_mac_address()
        self._attr_icon = "mdi:refresh"
        self._attr_name = "Refresh device info"

        self._attr_device_info = {"identifiers": {("edilkamin", self._mac_address)}}

    @property
    def unique_id(self) -> str:
        """Return a unique_id for this entity."""
        return f"{self._mac_address}_refresh_button"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Manual refresh requested for device %s", self._mac_address)
        await self.coordinator.async_refresh()
        _LOGGER.info("Device info refreshed successfully")

