"""Application Credentials support for Hisense AC Plugin."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .const import CLIENT_ID, CLIENT_SECRET, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from .oauth2 import HisenseOAuth2Implementation

_LOGGER = logging.getLogger(__name__)


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return auth implementation for a credential."""
    return HisenseOAuth2Implementation(hass)
