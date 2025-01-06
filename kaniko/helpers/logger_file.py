import logging
import enum
from typing import Optional

from kaniko.models.model_wrapper import CommandLineOptions

DEFAULT_LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


class VerbosityLevel(enum.IntEnum):
    QUIET = -1
    NORMAL = 0
    VERBOSE = 1
    DEBUG = 2
    MAX = DEBUG

    @classmethod
    def from_opts(cls, opts: dict):
        if opts.get("--quiet"):
            return cls.QUIET
        verbosity_level = opts.get("-v", 0)
        return cls(min(verbosity_level, cls.MAX))


class Logger:
    _instance: Optional[logging.Logger] = None

    @classmethod
    def get_logger(
        cls, verbosity: VerbosityLevel = VerbosityLevel.NORMAL
    ) -> logging.Logger:
        """Retrieve the configured logger instance."""
        if cls._instance is None:
            cls._instance = cls.configure_logging(verbosity)
        return cls._instance

    @staticmethod
    def configure_logging(verbosity: VerbosityLevel) -> logging.Logger:
        """Centralized logger configuration."""
        logger = logging.getLogger("KanikoBuilder")
        if not logger.handlers:
            level = (
                logging.INFO if verbosity >= VerbosityLevel.NORMAL else logging.ERROR
            )
            logger.setLevel(level)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            logger.addHandler(console_handler)

        return logger


def _init_log():
    Logger.get_logger(VerbosityLevel.NORMAL)


class LoggerModel:
    def __init__(self, verbosity_level: int = logging.INFO):
        self.logger = logging.getLogger("KanikoComposeWrapper")
        self.logger.setLevel(verbosity_level)
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log_info(self, message: str) -> None:
        """Log information messages."""
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        """Log error messages."""
        self.logger.error(message)

    def log_warning(self, message: str) -> None:
        """Log warning messages."""
        self.logger.warning(message)

    def log_build_details(self, opts: CommandLineOptions) -> None:
        self.log_info(f"📁 Using docker-compose file: {opts.compose_file}")
        self.log_info(f"🛠️ Kaniko executor image: {opts.kaniko_image}")
        if opts.push:
            self.log_info("📤 Images will be pushed to the registry after build.")
        elif opts.deploy:
            self.log_info("🌐 Images will be deployed to the registry after build.")
        elif opts.dry_run:
            self.log_info("🔍 Running in dry-run mode. No images will be pushed.")
        else:
            self.log_warning(
                "⚠️ No deployment action specified: images will neither be pushed nor deployed."
            )
