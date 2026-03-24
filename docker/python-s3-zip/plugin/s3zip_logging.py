import logging
import os
import sys
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# S3Zip log-level tuning
# ---------------------------------------------------------------------------
# All s3zip loggers live under the "s3zip" parent logger, making them easy
# to filter in log aggregators (grep for "s3zip").
#
# The level is controlled by the S3ZIP_LOG_LEVEL environment variable.
# Accepted values: DEBUG, INFO, WARNING, ERROR, CRITICAL (case-insensitive).
# Default: INFO.
#
# Examples:
#   S3ZIP_LOG_LEVEL=DEBUG   -> verbose per-call tracing (before/after every op)
#   S3ZIP_LOG_LEVEL=INFO    -> lifecycle events only (start/stop/upload/download)
#   S3ZIP_LOG_LEVEL=WARNING -> only problems
# ---------------------------------------------------------------------------

# Here's the rationale:
#
# **The problem:**
# `logging.basicConfig()` has a well-known gotcha --- it only does anything
# **the first time it's called** on the root logger. Specifically, if the root
# logger (`logging.getLogger()`) already has at least one handler attached,
# `basicConfig()` silently does nothing (it's a no-op).
#
# **Why this matters in Orthanc:**
# The s3zip plugin runs inside Orthanc's Python plugin host, where
# **other plugins load first**. In particular, `plugin_lib.config`
# (from the `o8t_utility_plugin` package) likely calls `logging.basicConfig()`
# during its own initialization. By the time the s3zip plugin initializes:
#
# 1.  The root logger already has a handler (configured by `plugin_lib.config`).
#
# 2.  Any subsequent `logging.basicConfig()` call from s3zip would be
#     **silently ignored**.
#
# 3.  The s3zip plugin would have no control over its own log level, format,
#     or output destination.
#
# **The solution in this file:** Instead of calling `basicConfig()`, the code:
#
# -   Creates a **dedicated named logger** (`s3zip`) at line 48
# -   Attaches its **own handler** directly to that logger
# -   Sets `propagate = False` to prevent messages from bubbling up
#     to the root logger (which avoids duplicate output from whatever handler
#     `plugin_lib.config` set up)
#
# This gives the s3zip plugin **fully independent logging** --- its own level,
# its own format, its own output stream --- regardless of what any other plugin
# or the Orthanc host has already done to the root logger.
#
# **After `inject_logger_factory()` is called** (from `o8t_orthanc_plugin.py`),
# the s3zip-specific handler is removed and `propagate` is set to True so that
# all s3zip messages flow through the root logger's JSON formatter instead.

_S3ZIP_ROOT_LOGGER_NAME = "s3zip"
_LOG_LEVEL_ENV_VAR = "S3ZIP_LOG_LEVEL"
_DEFAULT_LOG_LEVEL = "INFO"

_initialized = False


def _ensure_s3zip_logging():
    """Set up the ``s3zip`` logger hierarchy exactly once.

    This avoids relying on ``logging.basicConfig`` which is a no-op when the
    root logger already has handlers (common inside Orthanc's Python plugin
    environment where plugin_lib.config may have already called basicConfig).
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    level_name = os.environ.get(_LOG_LEVEL_ENV_VAR, _DEFAULT_LOG_LEVEL).upper()
    level = getattr(logging, level_name, None)
    if level is None:
        level = logging.DEBUG
        # Can't use the logger yet, write directly to stderr
        print(f"[s3zip] WARNING: invalid {_LOG_LEVEL_ENV_VAR}={level_name!r}, "
              f"falling back to DEBUG", file=sys.stderr)

    s3zip_root = logging.getLogger(_S3ZIP_ROOT_LOGGER_NAME)
    s3zip_root.setLevel(level)

    # Only add a handler if one hasn't been added yet (idempotent)
    if not s3zip_root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s (pid=%(process)d tid=%(thread)d): %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        s3zip_root.addHandler(handler)

    # Prevent messages from propagating to root logger (avoids duplicate output
    # if the Orthanc environment also has a root handler).
    s3zip_root.propagate = False

    # Diagnostic: this line bypasses the logging framework entirely so it
    # always shows up in stderr, even if logging is misconfigured.
    print(f"[s3zip] logging initialized | level={logging.getLevelName(level)} "
          f"({_LOG_LEVEL_ENV_VAR}={os.environ.get(_LOG_LEVEL_ENV_VAR, '<unset, using default>')})",
          file=sys.stderr)


def inject_logger_factory(factory: Callable[[str], logging.Logger]) -> None:
    """Switch s3zip loggers to use the shared root logger (JSON-formatted).

    Call this from ``o8t_orthanc_plugin.py`` after importing the s3zip plugin
    and after ``plugin_lib.config`` has set up JSON logging on the root logger.

    Effect:
    - Removes the s3zip root logger's own stderr/text handler.
    - Sets ``propagate = True`` so all ``s3zip.*`` messages flow through to the
      root logger, which already has a :class:`JsonLogFormatter` handler.
    - Existing :class:`HybridLogger` instances in every module automatically
      benefit because they wrap standard-library :class:`logging.Logger` objects
      — once the ``s3zip`` parent propagates, their output is JSON-formatted.

    The ``factory`` argument is accepted for API clarity (it mirrors how the
    rest of the plugin creates loggers via ``config.get_logger``).  The key
    action is the logger reconfiguration, not creating new logger instances.
    """
    _ensure_s3zip_logging()  # make sure level is already set

    s3zip_root = logging.getLogger(_S3ZIP_ROOT_LOGGER_NAME)
    # Remove the s3zip-specific handler (stderr, text format).
    s3zip_root.handlers.clear()
    # Let messages propagate to the root logger (JSON-formatted by plugin_lib).
    s3zip_root.propagate = True
    # Note: the level on s3zip_root is preserved — it still controls which
    # messages are forwarded (e.g. DEBUG vs INFO).

    print("[s3zip] inject_logger_factory: s3zip loggers now propagate to root "
          "(JSON output via plugin_lib.config)", file=sys.stderr)


def _format_structured_values(kwargs: dict) -> str:
    """Format key-value pairs for embedding in the log message string.

    String values are quoted, numeric and other values are left bare.
    Example output: "file"="some/thing" "size"=543345

    The embedded string is intentionally kept so that plain-text grep on
    container logs still works alongside Datadog structured-field search.
    """
    parts = []
    for k, v in kwargs.items():
        if isinstance(v, str):
            parts.append(f'"{k}"="{v}"')
        else:
            parts.append(f'"{k}"={v}')
    return " ".join(parts)


class HybridLogger:
    """Logger that embeds structured data both in the message string and as
    extra fields on the LogRecord.

    Usage::

        logger = get_logger(__name__)
        logger.info("zip file uploaded", file="some/thing", size=543345)

    This produces a log message like::

        zip file uploaded | "file"="some/thing" "size"=543345

    *and* attaches ``file`` and ``size`` as structured fields on the
    LogRecord (accessible to JSON formatters / Datadog agent).

    The dual representation is intentional: the embedded string allows plain
    ``grep`` on container logs, while the structured fields enable Datadog
    faceted search without parsing.
    """

    def __init__(self, inner: logging.Logger):
        self._logger = inner

    # -- public property so callers can still inspect / change the level ------
    @property
    def level(self):
        return self._logger.level

    def setLevel(self, level):
        self._logger.setLevel(level)

    def isEnabledFor(self, level):
        return self._logger.isEnabledFor(level)

    # -- core log dispatch ----------------------------------------------------
    def _log(self, level: int, msg: str, kwargs: dict):
        if not self._logger.isEnabledFor(level):
            return
        if kwargs:
            structured_str = _format_structured_values(kwargs)
            full_msg = f"{msg} | {structured_str}"
        else:
            full_msg = msg
        # stacklevel=3: self._logger.log -> _log -> info/debug/… -> caller
        self._logger.log(level, full_msg, extra=kwargs, stacklevel=3)

    # -- convenience methods --------------------------------------------------
    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, kwargs)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, kwargs)

    def exception(self, msg: str, **kwargs):
        """Like ``error`` but also captures the current exception traceback."""
        if not self._logger.isEnabledFor(logging.ERROR):
            return
        if kwargs:
            structured_str = _format_structured_values(kwargs)
            full_msg = f"{msg} | {structured_str}"
        else:
            full_msg = msg
        self._logger.exception(full_msg, extra=kwargs, stacklevel=2)


def get_logger(name: str) -> HybridLogger:
    """Return a :class:`HybridLogger` wrapping a ``logging.Logger`` under the
    ``s3zip`` hierarchy.

    The returned logger's full name will be ``s3zip.<name>``, making it easy
    to spot in aggregated logs and to control via :data:`S3ZIP_LOG_LEVEL`.
    """
    _ensure_s3zip_logging()
    qualified = f"{_S3ZIP_ROOT_LOGGER_NAME}.{name}" if not name.startswith(_S3ZIP_ROOT_LOGGER_NAME) else name
    return HybridLogger(logging.getLogger(qualified))
