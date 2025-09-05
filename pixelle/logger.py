# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import logging


class HealthCheckFilter(logging.Filter):
    """Filter health check access logs"""

    def filter(self, record):
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            # filter health check access logs
            if 'GET /health HTTP/1.1' in message:
                return False
        return True


# apply filter to access logger
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

# set engineio and socketio log level
logging.getLogger("socketio").setLevel(logging.WARNING)
logging.getLogger("engineio").setLevel(logging.WARNING)
logging.getLogger("numexpr").setLevel(logging.WARNING)

# log config
logger_level = logging.INFO
logging.basicConfig(
    level=logger_level,
    format='%(asctime)s- %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

logger = logging.getLogger("PM")
logger.setLevel(logger_level)
