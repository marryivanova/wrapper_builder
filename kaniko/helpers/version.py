import importlib.metadata
import logging

logger = logging.getLogger(__name__)

# Script version
SCRIPT_VERSION = "1.1.0.0"


def version_lib(package_name: str, default: str = "<UNDEFINED>"):
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return default
