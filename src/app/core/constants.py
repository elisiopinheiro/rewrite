"""Regex constants for schema validation."""

from app.core.config import settings

# ADGR group regex is configurable via env var for different environments
ADGR_GROUP_REGEX = settings.ADGR_GROUP_REGEX
CONSUMED_BY_REGEX = r"^APPD-[0-9]+$"
K8S_RESOURCES_NAME_REGEX = r"^([a-z0-9][a-z0-9-]?)*[a-z0-9]$"
