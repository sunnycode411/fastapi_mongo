import contextvars
import threading
from uuid import uuid4
import traceback
import sys

import logging
import logging.config
from fastapi import Request
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

from core.settings import LOGGING_LEVEL, LOGGING_FORMAT, LOGS_DIR


max_log_size = 100 * 1024 * 1024

# Context variable for request_id
request_id_var = contextvars.ContextVar("request_id", default=None)


async def request_logger(request: Request, call_next):
    """Middleware to log incoming requests and responses in JSON format."""
    logger = logging.getLogger("request_logger")
    logger.setLevel(LOGGING_LEVEL)

    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        file_handler = RotatingFileHandler(
            filename=LOGS_DIR / "request_logs" / "request.log",
            mode="w",
            maxBytes=max_log_size,
            backupCount=5,
        )
        formatter = jsonlogger.JsonFormatter(LOGGING_FORMAT)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    client_ip = request.client.host if request.client else "Unknown IP"
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request_id_var.set(request_id)

    logger.info(
        "Received request",
        extra={
            "request_id": request_id,
            "ip_address": client_ip,
            "method": request.method,
            "url": str(request.url),
        },
    )

    response = await call_next(request)

    logger.info(
        "Response sent",
        extra={
            "request_id": request_id,
            "ip_address": client_ip,
            "status_code": response.status_code,
        },
    )
    return response


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON log formatter."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["logger_name"] = record.name
        log_record["module"] = record.module
        request_id = request_id_var.get()
        if request_id:
            log_record["request_id"] = request_id


class AsyncLogger:
    """
    Asynchronous logger class to log messages to a file and console.
    This class is a singleton, and the same instance is returned for a given logger_name.
    """

    _instances = {}  # Singleton instances per logger_name
    _lock = threading.Lock()  # Thread-safe lock

    def __new__(cls, logger_name="service"):
        """
        Ensure a single instance of AsyncLogger per logger_name.

        This method implements the singleton pattern to guarantee that only
        one instance of AsyncLogger exists for each logger_name. It ensures
        thread-safe instantiation and initializes the logger if it doesn't
        already exist.

        Args:
            logger_name (str): The name of the logger. Defaults to "service_logger".

        Returns:
            AsyncLogger: The singleton instance for the specified logger_name.
        """

        with cls._lock:
            if logger_name not in cls._instances:
                instance = super().__new__(cls)
                instance._init_logger(logger_name)
                cls._instances[logger_name] = instance
            return cls._instances[logger_name]

    def _init_logger(self, logger_name):
        """
        Initializes the logger with the specified logger name.

        This method sets up a logger with both a file handler and a stream handler.
        The file handler writes log messages to a file with rotation, while the
        stream handler outputs log messages to the console. The log format is
        customized for both handlers to include timestamp, log level, and message.

        Args:
            logger_name (str): The name of the logger to initialize.
        """

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(LOGGING_LEVEL)

        if not self.logger.hasHandlers():  # Ensure handlers are added only once
            file_handler = RotatingFileHandler(
                LOGS_DIR / "service_logs" / f"{logger_name}.log",
                maxBytes=max_log_size,
                backupCount=5,
            )
            file_handler.setFormatter(
                CustomJsonFormatter(LOGGING_FORMAT)
            )
            self.logger.addHandler(file_handler)

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(
                logging.Formatter("[%(levelname)s] %(message)s")
            )
            self.logger.addHandler(stream_handler)

    def _should_log(self, level: str):
        """Check if the log level is high enough to be logged."""
        return getattr(logging, level.upper()) >= getattr(logging, LOGGING_LEVEL)

    async def _log(self, level, message, exc_info=False, **kwargs):
        """Internal async logging method."""
        if not self._should_log(level):
            return

        request_id = request_id_var.get()
        if request_id:
            kwargs["request_id"] = request_id

        # Ensure exception details are included
        if exc_info:
            exception_type, exception_value, tb = exc_info if isinstance(exc_info, tuple) else sys.exc_info()
            kwargs["exception"] = str(exception_value)  # Store the error message in structured logs
            kwargs["exception_type"] = str(exception_type)  # Store the exception type
            kwargs["traceback"] = traceback.format_exc()  # Store the full traceback
        
        # Select the log method
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        
        # Log with structured `extra`
        log_method(message, extra=kwargs)


    async def info(self, message, **kwargs):
        """
        Logs a message with level INFO.

        Args:
            message (str): The message to log.
            **kwargs: Additional keyword arguments to include in the log message.
        """
        await self._log("INFO", message, **kwargs)

    async def debug(self, message, **kwargs):
        """
        Logs a message with level DEBUG.

        Args:
            message (str): The message to log.
            **kwargs: Additional keyword arguments to include in the log message.
        """
        await self._log("DEBUG", message, **kwargs)

    async def warning(self, message, **kwargs):
        """
        Logs a message with level WARNING.

        Args:
            message (str): The message to log.
            **kwargs: Additional keyword arguments to include in the log message.
        """

        await self._log("WARNING", message, **kwargs)

    async def error(self, message, **kwargs):
        """
        Logs a message with level ERROR.

        Args:
            message (str): The message to log.
            **kwargs: Additional keyword arguments to include in the log message.
        """

        await self._log("ERROR", message, **kwargs)

    async def critical(self, message, **kwargs):
        """
        Logs a message with level CRITICAL.

        Args:
            message (str): The message to log.
            **kwargs: Additional keyword arguments to include in the log message.
        """
        await self._log("CRITICAL", message, **kwargs)

    async def exception(self, message, **kwargs):
        """
        Logs a message with level ERROR and includes exception information.

        Args:
            message (str): The message to log.
            **kwargs: Additional keyword arguments to include in the log message.
        """
        await self._log("ERROR", message, exc_info=True, **kwargs)


# Instantiate a global logger
service_logger = AsyncLogger()
