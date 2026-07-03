import logging
from datetime import datetime, timezone

from pythonjsonlogger.json import JsonFormatter

from app.config import settings

logger = logging.getLogger("app")
log_handler = logging.StreamHandler()


class CustomJsonFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            log_record["timestamp"] = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        level = log_record.get("level") or record.levelname
        log_record["level"] = level.upper()


formatter = CustomJsonFormatter(
    fmt="%(timestamp)s %(level)s %(module)s %(funcName)s",
)


log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(settings.LOG_LEVEL)