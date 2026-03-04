"""Device schema models using pydantic."""

from __future__ import annotations

import logging
from functools import cached_property
from typing import Any, Dict, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)

_LOGGER = logging.getLogger(__name__)


class DeviceAttribute(BaseModel):
    """Single device attribute with typed validation."""

    model_config = ConfigDict(frozen=False)

    key: str
    name: str
    attr_type: Literal["Number", "Enum"]
    step: int = 1
    value_range: Optional[str] = None
    value_map: Optional[Dict[str, str]] = None
    read_write: Literal["R", "RW"] = "RW"

    @model_validator(mode="after")
    def _check_enum_has_map(self) -> DeviceAttribute:
        """Warn if an Enum attribute has no value_map."""
        if self.attr_type == "Enum" and not self.value_map:
            _LOGGER.debug("Enum attribute %s has no value_map", self.key)
        return self

    @computed_field
    @cached_property
    def ranges(self) -> list[tuple[float, float]]:
        """Parsed (min, max) tuples from value_range.

        "16~32,61~90" -> [(16.0, 32.0), (61.0, 90.0)]
        Enum-style "0,1,2" or None -> []
        """
        if not self.value_range:
            return []
        result: list[tuple[float, float]] = []
        for segment in self.value_range.split(","):
            segment = segment.strip()
            if "~" in segment:
                parts = segment.split("~", 1)
                try:
                    result.append((float(parts[0]), float(parts[1])))
                except (ValueError, IndexError):
                    pass
        return result

    @property
    def is_read_only(self) -> bool:
        """True if attribute cannot be written."""
        return self.read_write == "R"

    @property
    def is_writable(self) -> bool:
        """True if attribute can be written."""
        return self.read_write == "RW"

    def parse_value(self, raw_value: Any) -> Any:
        """Convert a raw status value to its typed/mapped form."""
        if self.value_map and raw_value in self.value_map:
            return self.value_map[raw_value]
        if self.attr_type == "Number":
            return float(raw_value)
        return raw_value

    def is_valid_value(self, value: Any) -> bool:
        """Check if value is acceptable for this attribute."""
        if self.is_read_only:
            return False
        if self.ranges:
            try:
                v = float(value)
                return any(lo <= v <= hi for lo, hi in self.ranges)
            except (ValueError, TypeError):
                return False
        if self.value_map:
            return str(value) in self.value_map
        return True

    def reverse_lookup(self, display_value: str) -> Optional[str]:
        """Find the raw key for a display value (e.g. "制冷" -> "2")."""
        if not self.value_map:
            return None
        for k, v in self.value_map.items():
            if v == display_value:
                return k
        return None


class DeviceSchema(BaseModel):
    """Describes a device's attributes, value types, and valid ranges.

    Not subclassed — instantiated directly per device profile.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    device_type: str
    feature_code: str = ""
    attributes: Dict[str, DeviceAttribute] = Field(default_factory=dict)

    def remove_attribute(self, key: str) -> None:
        """Remove an attribute by key."""
        self.attributes.pop(key, None)

    def filter_attributes(self, property_list: list[dict]) -> None:
        """Filter attributes to those in property_list.

        Updates value_range/value_map from the API's propertyValueList.
        """
        prop_map: dict[str, Optional[str]] = {}
        for prop in property_list:
            if isinstance(prop, dict) and "propertyKey" in prop:
                prop_map[prop["propertyKey"]] = prop.get("propertyValueList")

        filtered: Dict[str, DeviceAttribute] = {}
        for key, value_list in prop_map.items():
            if key not in self.attributes:
                continue
            attr = self.attributes[key]

            if value_list:
                attr.value_range = value_list
                if attr.value_map:
                    allowed = set(value_list.split(","))
                    attr.value_map = {
                        k: v for k, v in attr.value_map.items() if k in allowed
                    }

            filtered[key] = attr

        self.attributes = filtered

    def ensure_attribute(self, key: str, attr: DeviceAttribute) -> None:
        """Add an attribute if not already present."""
        if key not in self.attributes:
            self.attributes[key] = attr

    def parse_status(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw device status into typed values."""
        parsed: Dict[str, Any] = {}
        for key, attr in self.attributes.items():
            if key not in status:
                continue
            try:
                parsed[key] = attr.parse_value(status[key])
            except (ValueError, TypeError) as err:
                _LOGGER.warning(
                    "Failed to parse %s (%s) value %s: %s",
                    key,
                    attr.name,
                    status[key],
                    err,
                )
        return parsed

    def validate_value(self, key: str, value: Any) -> bool:
        """Validate a control value for the given attribute key."""
        attr = self.attributes.get(key)
        if not attr:
            _LOGGER.warning(
                "Attribute %s not found in %s-%s",
                key,
                self.device_type,
                self.feature_code,
            )
            return False
        valid = attr.is_valid_value(value)
        if not valid:
            _LOGGER.warning(
                "Invalid value %s for %s (%s)",
                value,
                key,
                attr.name,
            )
        return valid
