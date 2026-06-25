from logging.config import dictConfig
import logging
import watchtower
import boto3
import os
from pathlib import Path

LOG_DIR = "logs"
Path(LOG_DIR).mkdir(exist_ok=True)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "daily_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": f"{LOG_DIR}/scl-api.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,  # Keeps last 7 days of logs
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console", "daily_file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console", "daily_file"],
            "level": "WARNING",  # atau ERROR
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console", "daily_file"],
            "level": "WARNING",  # khusus log akses HTTP
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "daily_file"],
            "level": "WARNING",  # khusus log error
            "propagate": False,
        },
        "watchfiles": {
            "handlers": ["console", "daily_file"], # atau handler yang Anda inginkan
            "level": "WARNING",  # Hanya log WARNING dan ERROR yang akan muncul
            "propagate": False,
        },
        "watchfiles.main": {
            "handlers": ["console", "daily_file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "daily_file"],
        "level": "INFO",
    },
}

#setup logger
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("scl-api")
logger.setLevel(logging.INFO)

#add cloudwatch handler
if not logger.handlers:
    # if os.getenv("ENVIRONTMENT").capitalize() == "AWS":
    #     cw_log_group = os.getenv("CW_LOG_GROUP")
    #     cw_stream_name = os.getenv("CW_STREAM_NAME")
    #     cw_boto3_name = os.getenv("CW_BOTO3_NAME")
    #     cw_region = os.getenv("CW_REGION_NAME")

    #     if all([cw_log_group, cw_stream_name, cw_boto3_name, cw_region]):
    #         try:
    #             cw_handler = watchtower.CloudWatchLogHandler(
    #                 log_group=cw_log_group,
    #                 boto3_client=boto3.client(cw_boto3_name, region_name=cw_region),
    #                 stream_name=cw_stream_name
    #             )
    #             logger.addHandler(cw_handler)
    #             logger.info("CloudWatch handler initialized successfully.")
    #         except Exception as e:
    #             # Fallback to console if CloudWatch fails
    #             logger.addHandler(logging.StreamHandler())
    #             logger.error(f"Failed to initialize CloudWatch handler: {e}. Falling back to console.")
    #     else:
    #         logger.addHandler(logging.StreamHandler())
    #         logger.warning("Missing CloudWatch environment variables. Falling back to console.")
    # else:
        #add console handler for local debugging
        logger.addHandler(logging.StreamHandler())