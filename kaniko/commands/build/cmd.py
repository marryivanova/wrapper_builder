"""
EpicMorg: Kaniko-Compose Wrapper

Usage:
    kaniko [--compose-file=<file>] build [--kaniko-image=<image>] [--push | --deploy | --dry-run] [--version] [--help]

Options:
  --compose-file=<file>           Path to the docker-compose.yml file. [default: docker-compose.yml]
  --kaniko-image=<image>          Kaniko executor image for building. [default: gcr.io/kaniko-project/executor:latest]
  --push, -p                      Push the built images to a registry.
  --deploy, -d                    Deploy images to the registry after building.
  --dry-run, --dry                Run in test mode: build images without pushing, with cleanup.
  --version, -v                   Show script version.
  -h --help                       Show this help message and exit.
"""

import logging
import typing as t

from kaniko.helpers.logger_file import VerbosityLevel, configure_logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run(opts: t.Dict[str, t.Any]) -> None:
    """Run the Kaniko-Compose Wrapper with dynamic verbosity."""
    verbosity = opts.get("verbosity", VerbosityLevel.NORMAL)
    configure_logging(verbosity)

    logger = logging.getLogger("KanikoComposeWrapper")
    logger.info("🚀 Starting Kaniko build process...")

    compose_file = opts.get("--compose-file", "docker-compose.yml")
    kaniko_image = opts.get("--kaniko-image", "gcr.io/kaniko-project/executor:latest")
    push = opts.get("--push", False)
    deploy = opts.get("--deploy", False)
    dry_run = opts.get("--dry-run", False)

    if opts.get("--version", False):
        logger.info("📄 Kaniko Builder Version: 1.0.0")
        return

    logger.info(f"📁 Using docker-compose file: {compose_file}")
    logger.info(f"🛠️ Kaniko executor image: {kaniko_image}")

    if push:
        logger.info("📤 Images will be pushed to the registry after build.")
    elif deploy:
        logger.info("🌐 Images will be deployed to the registry after build.")
    elif dry_run:
        logger.info("🔍 Running in dry-run mode. No images will be pushed.")
    else:
        logger.warning(
            "⚠️ No deployment action specified: images will neither be pushed nor deployed."
        )

    # Simulate error for testing verbosity
    if not compose_file:
        logger.error(
            "❌ Docker Compose file path is missing. "
            "Please provide a valid file with the --compose-file option. "
        )
        return

    if not kaniko_image:
        logger.error(
            "❌ Kaniko executor image is missing. "
            "Please provide a valid image with the --kaniko-image option."
        )
        return

    logger.debug("⚙️ Preparing Kaniko build with options...")
    logger.info("⚙️ Kaniko build process is now running... (details not implemented).")

    logger.info("✅ Kaniko build process completed successfully!")
