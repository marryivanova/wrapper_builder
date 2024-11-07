import importlib.metadata
import logging

from kaniko.settings import SCRIPT_VERSION

logger = logging.getLogger(__name__)


def version_lib(package_name: str, default: str = "<UNDEFINED>"):
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return default


def show_version() -> None:
    """Function to display the version of the script or package"""
    logger.info(f"Kaniko Builder Version: {SCRIPT_VERSION}")
