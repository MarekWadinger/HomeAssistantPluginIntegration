"""Device parsers package."""

import logging
from typing import Dict, Type

from .atw_035_699 import SplitWater035699Parser
from .base import BaseDeviceParser
from .base_bean import BaseBeanParser
from .bean_006_299 import Split006299Parser
from .hum_007 import Humidity007Parser

_LOGGER = logging.getLogger(__name__)

# Registry of device parsers
DEVICE_PARSERS: Dict[tuple[str, str], Type[BaseDeviceParser]] = {
    ("035", "699"): SplitWater035699Parser,
    ("006", "299"): Split006299Parser,
    ("007", ""): Humidity007Parser,
}


def get_device_parser(
    device_type: str, feature_code: str
) -> Type[BaseDeviceParser]:
    """Get device parser for the given device type."""
    _LOGGER.debug("Getting device parser for type %s", device_type)
    if DEVICE_PARSERS.get((device_type, feature_code)):
        _LOGGER.debug("三联供设备 %s", device_type)
        return DEVICE_PARSERS[(device_type, feature_code)]
    if device_type == "007":
        _LOGGER.debug("除湿机设备 %s", device_type)
        return Humidity007Parser
    # 预设的设备类型集合
    supported_device_types = ["009", "008", "006", "016"]
    if device_type in supported_device_types:
        _LOGGER.debug("Using default parser for device type %s", device_type)
        return BaseBeanParser
    else:
        _LOGGER.warning("Unsupported device type: %s", device_type)
        raise ValueError(f"Unsupported device type: {device_type}")
