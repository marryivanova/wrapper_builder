import logging
import enum
from typing import List, Literal


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


def configure_logging(verbosity: VerbosityLevel) -> None:
    def add_handlers_to_loggers(
        logger_names: List[str], severity: int
    ) -> List[logging.Logger]:
        loggers = [
            logging.getLogger(name)
            for name in logging.root.manager.loggerDict.keys()
            if name in logger_names
        ]
        for logger in loggers:
            # Add the console handler if it doesn't already exist
            if not any(
                isinstance(handler, logging.StreamHandler)
                for handler in logger.handlers
            ):
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
                logger.addHandler(console_handler)

            # Set the logger level based on severity
            logger.setLevel(severity)
        return loggers

    if verbosity == VerbosityLevel.QUIET:
        logging.disable(logging.CRITICAL)
        return

    # Configure console handler (this is a common handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    console_handler.setLevel(
        logging.DEBUG if verbosity >= VerbosityLevel.VERBOSE else logging.INFO
    )

    # Apply logging configurations to core and important loggers
    add_handlers_to_loggers(CORE_LOGGERS, LogSeverity.from_verbosity(verbosity, "core"))
    add_handlers_to_loggers(
        IMPORTANT_LOGGERS, LogSeverity.from_verbosity(verbosity, "important")
    )

    other_logger_names = [
        name
        for name in logging.root.manager.loggerDict.keys()
        if name.split(".")[0] not in CORE_LOGGERS + IMPORTANT_LOGGERS
    ]
    add_handlers_to_loggers(
        other_logger_names, LogSeverity.from_verbosity(verbosity, "general")
    )


def _configure_logging() -> logging.Logger:
    configure_logging(verbosity=VerbosityLevel.NORMAL)
    logger = logging.getLogger("KanikoBuilder")
    return logger
