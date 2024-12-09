import enum
import logging
from typing import Literal

DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
CORE_LOGGERS = ["core_logger"]
IMPORTANT_LOGGERS = ["important_logger"]


class VerbosityLevel(enum.IntEnum):
    QUIET = -1
    NORMAL = 0
    VERBOSE = 1
    VERY_VERBOSE = 2
    DEBUG = 3

    MAX = DEBUG

    @classmethod
    def from_opts(cls, opts: dict):
        def get_v_string(v: int) -> str:
            return "-" + "v" * v

        if opts.get("--quiet"):
            return cls.QUIET

        verbosity_level = opts.get("-v", 0)
        if verbosity_level > cls.MAX:
            current_verbosity_option, max_verbosity_option = get_v_string(
                verbosity_level
            ), get_v_string(cls.MAX)
            logging.error(
                f"Invalid verbosity option. Current verbosity option: {current_verbosity_option}, max verbosity option: {max_verbosity_option}"
            )
            return cls.QUIET

        return cls(verbosity_level)


class LogSeverity(enum.IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def from_verbosity(
        cls,
        verbosity: VerbosityLevel,
        category: Literal["core", "important", "general"],
    ) -> "LogSeverity":
        if verbosity == VerbosityLevel.QUIET:
            return cls.CRITICAL
        if verbosity == VerbosityLevel.NORMAL:
            return cls.INFO if category == "core" else cls.WARNING
        if verbosity == VerbosityLevel.VERBOSE:
            return cls.DEBUG if category == "core" else cls.INFO
        if verbosity == VerbosityLevel.VERY_VERBOSE:
            return cls.DEBUG if category in ["core", "important"] else cls.INFO
        return cls.DEBUG


def configure_logging(verbosity: VerbosityLevel) -> logging.Logger:
    """Centralized logger configuration."""
    logger = logging.getLogger("KanikoBuilder")
    if not logger.handlers:
        logger.setLevel(LogSeverity.from_verbosity(verbosity, "general"))

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        console_handler.setLevel(LogSeverity.from_verbosity(verbosity, "general"))
        logger.addHandler(console_handler)

    return logger


KANIKO_LOGGER = None


def get_logger(verbosity: VerbosityLevel = VerbosityLevel.NORMAL) -> logging.Logger:
    """Retrieve the configured logger instance."""
    global KANIKO_LOGGER
    if KANIKO_LOGGER is None:
        KANIKO_LOGGER = configure_logging(verbosity)
    return KANIKO_LOGGER


def _init_log():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger("KanikoBuilder")
