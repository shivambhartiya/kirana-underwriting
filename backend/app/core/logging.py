import logging
import sys

import structlog


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s")

