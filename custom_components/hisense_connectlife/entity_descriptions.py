"""Pydantic models for entity configuration descriptions."""

from __future__ import annotations

from pydantic import BaseModel

from homeassistant.components.number import NumberDeviceClass, NumberMode
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass


class SwitchEntityConfig(BaseModel):
    """Frozen configuration for a switch entity."""

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    key: str
    name: str
    icon_on: str
    icon_off: str
    description: str
    expected_value: str | None = None


class SensorEntityConfig(BaseModel):
    """Frozen configuration for a sensor entity."""

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    key: str
    name: str
    icon: str
    device_class: SensorDeviceClass
    state_class: SensorStateClass | None = None
    unit: str | None = None
    description: str


class NumberEntityConfig(BaseModel):
    """Frozen configuration for a number entity."""

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    key: str
    name: str
    icon: str
    device_class: NumberDeviceClass
    mode: NumberMode
    unit: str
    min_value: float
    max_value: float
    step: float
    description: str


def fault_sensor(key: str, name: str) -> SensorEntityConfig:
    """Create a fault sensor config with standard defaults."""
    return SensorEntityConfig(
        key=key,
        name=name,
        icon="mdi:alert",
        device_class=SensorDeviceClass.ENUM,
        description=name,
    )
