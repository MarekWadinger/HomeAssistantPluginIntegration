"""Data models for Hisense AC Plugin."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from homeassistant.exceptions import HomeAssistantError
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .const import DeviceType
from .devices import DeviceSchema

_LOGGER = logging.getLogger(__name__)

_SUPPORTED_TYPES = {"009", "008", "007", "006", "016", "035"}
_CLIMATE_TYPES = {"009", "008", "006"}
_WATER_TYPES = {"016"}
_HUMIDITY_TYPES = {"007"}


class ApiClientProtocol(Protocol):
    """Protocol for API client."""

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        _retry: bool = False,
    ) -> dict[str, Any]:
        """Make API request."""
        ...

    @property
    def oauth_session(self) -> Any:
        """Get OAuth session."""
        ...


class PushChannel(BaseModel):
    """Push channel information."""

    model_config = ConfigDict(populate_by_name=True)

    push_channel: str = Field(default="", alias="pushChannel")


class NotificationInfo(BaseModel):
    """Notification server information."""

    model_config = ConfigDict(populate_by_name=True)

    push_channels: list[PushChannel] = Field(
        default_factory=list, alias="pushChannels"
    )
    push_server_ip: str = Field(default="", alias="pushServerIp")
    push_server_port: str = Field(default="", alias="pushServerPort")
    push_server_ssl_port: str = Field(default="", alias="pushServerSslPort")
    hb_interval: int = Field(default=30, alias="hbInterval")
    hb_fail_times: int = Field(default=3, alias="hbFailTimes")
    has_msg_unread: int = Field(default=0, alias="hasMsgUnread")
    unread_msg_num: int = Field(default=0, alias="unreadMsgNum")


class DeviceInfo(BaseModel):
    """Device information from the ConnectLife API."""

    model_config = ConfigDict(populate_by_name=True)

    # Core identity
    device_id: str = Field(default="", alias="deviceId")
    puid: str = Field(default="")
    name: str = Field(default="", alias="deviceNickName")
    type_code: str = Field(default="", alias="deviceTypeCode")
    type_name: str = Field(default="", alias="deviceTypeName")
    feature_code: str = Field(default="", alias="deviceFeatureCode")
    feature_name: str = Field(default="", alias="deviceFeatureName")

    # Optional metadata (use Any for fields that may arrive as "" from API)
    wifi_id: str | None = Field(default=None, alias="wifiId")
    bind_time: Any = Field(default=None, alias="bindTime")
    role: Any = Field(default=None)
    room_id: Any = Field(default=None, alias="roomId")
    room_name: str | None = Field(default=None, alias="roomName")

    # Status
    status: dict[str, Any] = Field(default_factory=dict, alias="statusList")
    offline_state: int | None = Field(default=None, alias="offlineState")

    # Other
    use_time: Any = Field(default=None, alias="useTime")
    seq: Any = Field(default=None)
    create_time: Any = Field(default=None, alias="createTime")

    # Mutable non-API fields
    failed_data: list[str] = Field(default_factory=list, exclude=True)

    @field_validator("offline_state", mode="before")
    @classmethod
    def _coerce_offline_state(cls, v: Any) -> int | None:
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    @field_validator("status", mode="before")
    @classmethod
    def _coerce_status(cls, v: Any) -> dict[str, Any]:
        if isinstance(v, dict):
            return v
        _LOGGER.warning("Invalid status data: %s", v)
        return {}

    @property
    def is_online(self) -> bool:
        """Device is considered online if it has status data.

        The API's offlineState field is unreliable — devices actively
        reporting sensor data (f_temp_in, f_votage, etc.) still return
        offlineState=1.  Fall back to checking whether we have any
        status payload at all.
        """
        return bool(self.status)

    @property
    def is_on(self) -> bool:
        """Device power is on (t_power == '1')."""
        power = self.status.get("t_power")
        return power == 1 or power == "1"

    # Keep backward compat alias
    is_onOff = is_on

    def get_device_type(self) -> DeviceType | None:
        """Get device type information."""
        if not self.type_code or not self.feature_code:
            _LOGGER.warning(
                "Cannot get device type: type_code=%s, feature_code=%s",
                self.type_code,
                self.feature_code,
            )
            return None
        return DeviceType(
            type_code=self.type_code,
            feature_code=self.feature_code,
            description=self.name,
        )

    def is_supported(self) -> bool:
        """Check if this device type is a supported climate device."""
        return self.type_code in _CLIMATE_TYPES

    def is_devices(self) -> bool:
        """Check if this device type is any supported type."""
        return self.type_code in _SUPPORTED_TYPES

    def is_water(self) -> bool:
        """Check if this is a water heater device."""
        return self.type_code in _WATER_TYPES

    def is_humidityr(self) -> bool:
        """Check if this is a dehumidifier device."""
        return self.type_code in _HUMIDITY_TYPES

    def get_status_value(self, key: str, default: Any = None) -> Any:
        """Get value from status dict."""
        return self.status.get(key, default)

    def has_attribute(self, key: str, parser: DeviceSchema) -> bool:
        """Check if device has a specific attribute."""
        if parser and parser.attributes:
            return key in parser.attributes
        return key in self.status

    def to_dict(self) -> dict[str, Any]:
        """Serialize to API-compatible dict (camelCase keys)."""
        return self.model_dump(by_alias=True, exclude={"failed_data"})

    def debug_info(self) -> str:
        """Return detailed debug information about the device."""
        return "\n".join(
            [
                f"Device: {self.name} ({self.device_id})",
                f"PUID: {self.puid}",
                f"Type: {self.type_code}-{self.feature_code}"
                f" ({self.type_name} - {self.feature_name})",
                f"Online: {self.is_online} (offline_state: {self.offline_state})",
                f"Status: {self.status}",
                f"Supported: {self.is_supported()}",
            ]
        )


class HisenseApiError(HomeAssistantError):
    """Raised when API request fails."""
