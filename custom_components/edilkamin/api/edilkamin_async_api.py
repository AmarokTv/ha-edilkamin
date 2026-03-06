import logging
from typing import Any

from custom_components.edilkamin.external_edilkamin import (
    device_info,
    mqtt_command,
    sign_in,
)
from custom_components.edilkamin.const import (
    TEMP_MIN,
    TEMP_MAX,
    FAN_SPEED_MIN,
    FAN_SPEED_MAX,
    POWER_LEVEL_MIN,
    POWER_LEVEL_MAX,
    MQTT_COMMANDS,
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class EdilkaminAsyncApi:
    """Class to interact with the Edilkamin API."""

    def __init__(
        self, mac_address, username: str, password: str, hass: HomeAssistant
    ) -> None:
        """Initialize the class."""
        self._hass = hass
        self._mac_address = mac_address
        self._username = username
        self._password = password

    def get_mac_address(self):
        """Get the mac address."""
        return self._mac_address

    async def authenticate(self) -> bool:
        """Authenticate with the Edilkamin API."""
        try:
            _LOGGER.debug("Authenticating user: %s", self._username)
            await self._hass.async_add_executor_job(
                sign_in, self._username, self._password
            )
            _LOGGER.info("Successfully authenticated with Edilkamin API")
            return True
        except Exception as e:  # noqa: BLE001
            _LOGGER.error("Authentication failed: %s - %s", type(e).__name__, str(e))
            return False

    async def set_temperature(self, value: float) -> None:
        """Modify the temperature with validation."""
        if not isinstance(value, (int, float)):
            msg = f"Temperature must be numeric, got {type(value).__name__}"
            _LOGGER.error(msg)
            raise ValueError(msg)

        if not TEMP_MIN <= value <= TEMP_MAX:
            msg = f"Temperature {value} out of range [{TEMP_MIN}, {TEMP_MAX}]"
            _LOGGER.error(msg)
            raise ValueError(msg)

        _LOGGER.debug("Setting temperature to %s°C", value)
        await self.execute_command({"name": "enviroment_1_temperature", "value": value})

    async def enable_power(self):
        """Set the power status to on."""
        await self.execute_command({"name": "power", "value": 1})

    async def disable_power(self):
        """Set the power status to off."""
        await self.execute_command({"name": "power", "value": 0})

    async def enable_chrono_mode(self):
        """Enable the chrono mode."""
        await self.execute_command({"name": "chrono_mode", "value": True})

    async def disable_chrono_mode(self):
        """Disable the chono mode."""
        await self.execute_command({"name": "chrono_mode", "value": False})

    async def enable_airkare(self):
        """Enable airkare."""
        await self.execute_command({"name": "airkare_function", "value": 1})

    async def disable_airkare(self):
        """Disable airkare."""
        await self.execute_command({"name": "airkare_function", "value": 0})

    async def enable_relax(self):
        """Enable relax."""
        await self.execute_command({"name": "relax_mode", "value": True})

    async def disable_relax(self):
        """Disable relax."""
        await self.execute_command({"name": "relax_mode", "value": False})

    async def set_fan_speed(self, value: int, index: int = 1) -> None:
        """Set the speed of a fan with validation."""
        if not isinstance(value, int):
            msg = f"Fan speed must be integer, got {type(value).__name__}"
            _LOGGER.error(msg)
            raise ValueError(msg)

        if not FAN_SPEED_MIN <= value <= FAN_SPEED_MAX:
            msg = f"Fan speed {value} out of range [{FAN_SPEED_MIN}, {FAN_SPEED_MAX}]"
            _LOGGER.error(msg)
            raise ValueError(msg)

        if not isinstance(index, int) or index < 1 or index > 3:
            msg = f"Fan index must be 1-3, got {index}"
            _LOGGER.error(msg)
            raise ValueError(msg)

        _LOGGER.debug("Setting fan %d speed to %d%%", index, value)
        await self.execute_command(
            {"name": f"fan_{index}_speed", "value": int(value)}
        )


    async def get_token(self):
        return await self._hass.async_add_executor_job(
            sign_in, self._username, self._password
        )

    async def get_info(self) -> dict[str, Any]:
        """Get the device information with error handling."""
        try:
            token = await self.get_token()
            _LOGGER.debug("Fetching device info for MAC %s", self._mac_address)
            info = await self._hass.async_add_executor_job(
                device_info, token, self._mac_address
            )
            _LOGGER.debug("Device info fetched successfully")
            return info
        except Exception as e:
            msg = f"Failed to get device info: {type(e).__name__}: {str(e)}"
            _LOGGER.error(msg)
            raise

    async def enable_standby_mode(self):
        """Set the standby mode."""
        if not await self.is_auto():
            raise NotInRightStateError

        await self.execute_command({"name": "standby_mode", "value": True})

    async def disable_standby_mode(self):
        """Set the standby mode."""
        if not await self.is_auto():
            raise NotInRightStateError

        await self.execute_command({"name": "standby_mode", "value": False})

    async def is_auto(self) -> bool:
        """Check if the device is in auto mode with safe access."""
        try:
            info = await self.get_info()
            is_auto_mode = (
                info.get("nvm", {})
                .get("user_parameters", {})
                .get("is_auto", False)
            )
            _LOGGER.debug("Device auto mode: %s", is_auto_mode)
            return is_auto_mode
        except Exception as e:
            msg = f"Failed to check auto mode: {type(e).__name__}"
            _LOGGER.error(msg)
            return False

    async def enable_auto_mode(self):
        """Set the auto mode."""
        await self.execute_command({"name": "auto_mode", "value": True})

    async def disable_auto_mode(self):
        """Set the auto mode."""
        await self.execute_command({"name": "auto_mode", "value": False})

    async def set_manual_power_level(self, value: int) -> None:
        """Set the manual power level with validation."""
        if not isinstance(value, int):
            msg = f"Power level must be integer, got {type(value).__name__}"
            _LOGGER.error(msg)
            raise ValueError(msg)

        if not POWER_LEVEL_MIN <= value <= POWER_LEVEL_MAX:
            msg = f"Power level {value} out of range [{POWER_LEVEL_MIN}, {POWER_LEVEL_MAX}]"
            _LOGGER.error(msg)
            raise ValueError(msg)

        _LOGGER.debug("Setting manual power level to %d", value)
        await self.execute_command({"name": "power_level", "value": value})

    async def execute_command(self, payload: dict[str, Any]) -> Any:
        """Execute an MQTT command with validation."""
        # Validate command name
        command_name = payload.get("name")
        if command_name not in MQTT_COMMANDS:
            msg = f"Invalid MQTT command: {command_name}. Valid commands: {MQTT_COMMANDS}"
            _LOGGER.error(msg)
            raise ValueError(msg)

        token = await self.get_token()
        _LOGGER.debug("Executing MQTT command: %s with payload %s", command_name, payload)

        try:
            result = await self._hass.async_add_executor_job(
                mqtt_command, token, self._mac_address, payload
            )
            _LOGGER.info("Command %s executed successfully", command_name)
            return result
        except Exception as e:
            msg = f"Failed to execute command {command_name}: {type(e).__name__}"
            _LOGGER.error(msg)
            raise


class HttpError(Exception):
    """HTTP exception class with message text, and status code."""

    def __init__(self, message, text, status_code) -> None:
        """Initialize the class."""
        super().__init__(message)
        self.status_code = status_code
        self.text = text


class EdilkaminApiError(Exception):
    """Base class for exceptions in this module."""


class NotInRightStateError(EdilkaminApiError):
    """Exception raised when the device is not in the right state."""

    def __init__(self):
        super().__init__("Standby mode is only available from auto mode.")
