"""Device schema registry."""

import logging

from .atw_035_699 import ATW_035_699
from .base import DeviceSchema
from .base_bean import BASE_BEAN
from .bean_006_299 import SPLIT_006_299
from .hum_007 import HUMIDITY_007
from .split_ac_009_199 import SPLIT_AC_009_199
from .window_ac_008_399 import WINDOW_AC_008_399

_LOGGER = logging.getLogger(__name__)


# Registry: (device_type, feature_code) -> DeviceSchema template
_REGISTRY: dict[tuple[str, str], DeviceSchema] = {
    ("035", "699"): ATW_035_699,
    ("006", "299"): SPLIT_006_299,
    ("007", ""): HUMIDITY_007,
    ("009", "199"): SPLIT_AC_009_199,
    ("008", "399"): WINDOW_AC_008_399,
}

# Fallback device types that use BASE_BEAN
_BEAN_DEVICE_TYPES = {"009", "008", "006", "016"}


def get_device_schema(device_type: str, feature_code: str) -> DeviceSchema:
    """Get a fresh DeviceSchema copy for the given device type.

    Returns a deep copy so each device gets its own mutable instance.
    """
    schema = _REGISTRY.get((device_type, feature_code))
    if schema:
        return schema.model_copy(deep=True)

    if device_type == "007":
        return HUMIDITY_007.model_copy(deep=True)

    if device_type in _BEAN_DEVICE_TYPES:
        return BASE_BEAN.model_copy(deep=True)

    raise ValueError(f"Unsupported device type: {device_type}")
