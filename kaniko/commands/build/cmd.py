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
  -h --help                       Show this help message and exit.
"""

import logging
import subprocess
import typing as t
from kaniko import helpers
from kaniko.helpers.logger_file import VerbosityLevel
from kaniko.settings import SCRIPT_VERSION


def parse_options(opts: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Parse and validate options from the command line."""
    return {
        "compose_file": opts.get("--compose-file", "docker-compose.yml"),
        "kaniko_image": opts.get(
            "--kaniko-image", "gcr.io/kaniko-project/executor:latest"
        ),
        "push": opts.get("--push", False),
        "deploy": opts.get("--deploy", False),
        "dry_run": opts.get("--dry-run", False),
        "version": opts.get("--version", False),
    }


def validate_options(opts: t.Dict[str, t.Any], logger: logging.Logger) -> bool:
    """Validate required options and log errors if needed."""
    if not opts["compose_file"]:
        logger.error(
            "❌ Docker Compose file path is missing. "
            "Please provide a valid file with the --compose-file option."
        )
        return False

    if not opts["kaniko_image"]:
        logger.error(
            "❌ Kaniko executor image is missing. "
            "Please provide a valid image with the --kaniko-image option."
        )
        return False

    return True


def log_build_details(opts: t.Dict[str, t.Any], logger: logging.Logger) -> None:
    """Log detailed build settings."""
    logger.info(f"📁 Using docker-compose file: {opts['compose_file']}")
    logger.info(f"🛠️ Kaniko executor image: {opts['kaniko_image']}")
    if opts["push"]:
        logger.info("📤 Images will be pushed to the registry after build.")
    elif opts["deploy"]:
        logger.info("🌐 Images will be deployed to the registry after build.")
    elif opts["dry_run"]:
        logger.info("🔍 Running in dry-run mode. No images will be pushed.")
    else:
        logger.warning(
            "⚠️ No deployment action specified: images will neither be pushed nor deployed."
        )


def run_build(opts: t.Dict[str, t.Any], logger: logging.Logger) -> None:
    """Simulate the Kaniko build process and trigger it using subprocess."""
    logger.debug(
        "\n⚙️ Preparing Kaniko build with options...\n"
        f"compose_file: {opts['compose_file']}, \n"
        f"kaniko_image: {opts['kaniko_image']}, \n"
        f"push: {opts['push']}, \n"
        f"deploy: {opts['deploy']}, \n"
        f"dry_run: {opts['dry_run']}.\n"
    )

    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{opts['compose_file']}:/workspace",
        opts["kaniko_image"],
        "--context",
        "/workspace",
        "--dockerfile",
        "/workspace/Dockerfile",
    ]

    if opts["push"]:
        command.extend(["--destination", "your-registry/your-image:latest"])
    elif opts["deploy"]:
        command.extend(["--destination", "your-registry/your-image:latest", "--deploy"])

    if opts["dry_run"]:
        logger.info("🔍 Running in dry-run mode. No images will be pushed.")
        return

    try:
        logger.info("⚙️ Kaniko build process is now running...")
        subprocess.run(command, check=True)
        logger.info("✅ Kaniko build process completed successfully!")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Kaniko build failed with error: {e}")
        return


def run(opts: t.Dict[str, t.Any]) -> None:
    helpers.logger_file.configure_logging(verbosity=VerbosityLevel.NORMAL)
    logger = logging.getLogger("KanikoComposeWrapper")

    options = parse_options(opts)

    if options["version"]:
        logger.info(f"📄 Kaniko Builder Version: {SCRIPT_VERSION}")
        return

    logger.info("🚀 Starting Kaniko build process...")

    if not validate_options(options, logger):
        return

    log_build_details(options, logger)
    run_build(options, logger)
