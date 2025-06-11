# logging.py
import logging
import os
from threading import Lock
from logging.handlers import TimedRotatingFileHandler

from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get("", None)
APP_NAME = os.environ.get("", None)
LOG_FILE = os.environ.get("", None)


class AzureMonitorLoggingHandler(logging.Handler):
    _logger_provider = None
    _lock = Lock()

    def __init__(self, connection_string: str, thread: str = "main"):
        super().__init__()
        self.exporter = AzureMonitorLogExporter(connection_string=connection_string)
        self.thread = thread

        # Ensure LoggerProvider is created only once
        with self._lock:
            if AzureMonitorLoggingHandler._logger_provider is None:
                # Create a LoggerProvider with a resource specific to the thread
                resource = Resource.create({"service.name": APP_NAME})
                logger_provider = LoggerProvider(resource=resource)
                logger_provider.add_log_record_processor(BatchLogRecordProcessor(self.exporter))
                set_logger_provider(logger_provider)  # Set the LoggerProvider globally
                AzureMonitorLoggingHandler._logger_provider = logger_provider
            else:
                # Reuse the existing LoggerProvider
                logger_provider = AzureMonitorLoggingHandler._logger_provider

        # Create an OpenTelemetry LoggingHandler
        self.otlp_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

    def emit(self, record):
        try:
            # Add thread-specific information to the log record dynamically
            record.thread_name = self.thread
            self.otlp_handler.emit(record)
        except Exception as e:
            print(f"Failed to send log to Azure Monitor: {e}")


def setup_logging(thread: str = "main"):
    """
    Configure the root logger to log to the console, log file, and Azure Monitor.
    # TimedRotatingFileHandler: rotates logs daily and keeps 3 days of logs
    # Create formatters and add them to handlers
    # Add handlers to the root logger
    """

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Set the logging level for all logs

    # Console handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_formatter = logging.Formatter(log_format)
    c_handler.setFormatter(c_formatter)
    root_logger.addHandler(c_handler)

    # Log file handler
    if LOG_FILE:
        # Ensure the directory for the log file exists
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        # Ensure the log file exists
        if not os.path.isfile(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                pass  # Create an empty file
        f_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=3, encoding="utf-8")
        f_handler.setLevel(logging.INFO)
        f_formatter = logging.Formatter(log_format)
        f_handler.setFormatter(f_formatter)
        root_logger.addHandler(f_handler)

    # Azure Monitor Logging handler
    if APPLICATIONINSIGHTS_CONNECTION_STRING:
        ai_format_log = (
            "%(app_name)s | %(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s - %(funcName)s"
        )
        ai_formatter = logging.Formatter(ai_format_log)
        ai_handler = AzureMonitorLoggingHandler(APPLICATIONINSIGHTS_CONNECTION_STRING, thread)
        ai_handler.setFormatter(ai_formatter)
        root_logger.addHandler(ai_handler)
        root_logger.addFilter(AppNameFilter(app_name=APP_NAME))

    # Suppress logs from specific loggers
    logging.getLogger("azure.monitor.opentelemetry.exporter.export._base").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)

    return root_logger  # Return the root logger instance


class AppNameFilter(logging.Filter):
    def __init__(self, app_name):
        super().__init__()
        self.app_name = app_name

    def filter(self, record):
        record.app_name = self.app_name
        return True
