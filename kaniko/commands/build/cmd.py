"""
Kaniko-Compose Wrapper

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

import argparse
import logging
import subprocess
import typing as t

from kaniko.commands.build.kaniko.kaniko_wrapper import KanikoCommandBuilder
from kaniko.helpers.logger_file import LoggerModel
from kaniko.settings import SCRIPT_VERSION


class CommandLineOptions:
    def __init__(
        self,
        compose_file: str = "docker-compose.yml",
        kaniko_image: str = "gcr.io/kaniko-project/executor:latest",
        push: bool = False,
        deploy: bool = False,
        dry_run: bool = False,
        version: bool = False,
    ):
        self.compose_file = compose_file
        self.kaniko_image = kaniko_image
        self.push = push
        self.deploy = deploy
        self.dry_run = dry_run
        self.version = version

    @classmethod
    def from_dict(cls, opts: t.Dict[str, t.Any]) -> "CommandLineOptions":
        return cls(
            compose_file=opts.get("--compose-file", "docker-compose.yml"),
            kaniko_image=opts.get(
                "--kaniko-image", "gcr.io/kaniko-project/executor:latest"
            ),
            push=opts.get("--push", False),
            deploy=opts.get("--deploy", False),
            dry_run=opts.get("--dry-run", False),
            version=opts.get("--version", False),
        )

    def validate(self, logger: t.Optional[logging.Logger] = None) -> bool:
        if not self.compose_file:
            if logger:
                logger.error("❌ Docker Compose file path is missing.")
            return False
        if not self.kaniko_image:
            if logger:
                logger.error("❌ Kaniko image is missing.")
            return False
        return True


class KanikoBuildCommand:
    def __init__(self, opts: CommandLineOptions):
        self.opts = opts
        self.command_builder = KanikoCommandBuilder(self.opts.kaniko_image)

    def build_command(self) -> t.List[str]:
        return self.command_builder.build_command(
            context=self.opts.compose_file,
            dockerfile="Dockerfile",
            image=self.opts.kaniko_image,
            build_args={},
            push=self.opts.push,
        )

    def run_build(self, logger: LoggerModel) -> None:
        if self.opts.dry_run:
            logger.log_info("🔍 Running in dry-run mode. No images will be pushed.")
            return

        try:
            logger.log_info("⚙️ Kaniko build process is now running...")
            command = self.build_command()
            subprocess.run(command, check=True)
            logger.log_info("✅ Kaniko build process completed successfully!")
        except subprocess.CalledProcessError as e:
            logger.log_error(f"❌ Kaniko build failed with error: {e}")
        except Exception as e:
            logger.log_error(f"❌ An unexpected error occurred: {e}")


class VersionModel:
    def __init__(self, version: str):
        self.version = version

    def display_version(self, logger: LoggerModel) -> None:
        logger.log_info(f"📄 Kaniko Builder Script Version: {self.version}")


def run(opts: t.Dict[str, t.Any], script_version=SCRIPT_VERSION) -> None:
    logger = LoggerModel(logging.INFO)
    options = CommandLineOptions.from_dict(opts)

    if options.version:
        version_model = VersionModel(script_version)
        version_model.display_version(logger)
        return

    logger.log_info("🚀 Starting Kaniko build process...")

    if not options.validate(logger):
        return

    logger.log_build_details(options)

    build_command = KanikoBuildCommand(options)
    build_command.run_build(logger)
