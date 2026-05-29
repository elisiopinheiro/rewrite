from enum import Enum


class Provider(str, Enum):
    AWS = "aws"
    AZURE = "azure"


class Environment(str, Enum):
    TEST = "test"
    DEV = "development"
    INT = "integration"
    PRE_PROD = "pre-production"
    PROD = "production"


class ClusterStatus(str, Enum):
    RUNNING = "running"
    FREEZE = "freeze"


class AzureSkuTier(str, Enum):
    FREE = "Free"
    STANDARD = "Standard"


class LoggingLevel(str, Enum):
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"
    ERROR = "ERROR"
    WARN = "WARN"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    NOTSET = "NOTSET"
    DEFAULT = WARN

    def __str__(self):
        return self.value


class WebhookType(str, Enum):
    platform = "platform"
    customer = "customer"


class WebhookLevel(str, Enum):
    all = "all"
