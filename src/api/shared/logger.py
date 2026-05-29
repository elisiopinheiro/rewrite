import logging
from datetime import datetime, timezone

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


class MyLogger:
    _logger = None

    def __new__(cls, *args, **kwargs):
        if cls._logger is None:
            cls._logger = super().__new__(cls, *args, **kwargs)
            cls._logger = logging.getLogger("clusters-4wm")
            cls._logger.setLevel(logging.INFO)
            logHandler = logging.StreamHandler()
            formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
            logHandler.setFormatter(formatter)
            cls._logger.addHandler(logHandler)

        return cls._logger


logger = MyLogger()
