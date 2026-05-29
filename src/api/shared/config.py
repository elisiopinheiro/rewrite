import os
import re

ADGR_GROUP_REGEX = os.environ.get("ADGR_GROUP_REGEX", "").strip('"')

DEFAULT_LOCK_TIMEOUT_MINUTES = int(os.environ.get("LOCK_TIMEOUT_MINUTES", "360").strip())

APP_VERSION = os.environ.get("APP_VERSION", "development")

APP_ENVIRONMENT = os.environ.get("APP_ENVIRONMENT", "dev")

DATABASE_LOGGING_LEVEL = os.environ.get("DATABASE_LOGGING_LEVEL", "WARN").strip('"').upper()

DB_TABLE_RELATIONSHIP_DEFAULTS = {
    "cascade": "all, delete-orphan",
    "lazy": "joined",
}

K8S_RESOURCES_NAME_REGEX = r"^([a-z0-9][a-z0-9-]?)*[a-z0-9]$"
CONSUMED_BY_REGEX = "^APPD-[0-9]+$"

# Downscaler
SCALING_PERIOD_PATTERN = re.compile(
    r"^(?P<startweekday>[a-zA-Z]{3})-(?P<endweekday>[a-zA-Z]{3}) "
    r"(?P<starthour>(\d\d):(\d\d))-(?P<endhour>(\d\d):(\d\d)) "
    r"(?P<timezone>[a-zA-Z/_]+)$"
)
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
