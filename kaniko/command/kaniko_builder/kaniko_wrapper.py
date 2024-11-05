"""
EpicMorg: Kaniko-Compose Wrapper

Usage:
  kaniko [--compose-file=<file>] builder [--kaniko-image=<image>] [--push | --deploy | --dry-run] [--version] [--help]

Options:
  --compose-file=<file>    Path to the docker-compose.yml file [default: docker-compose.yml].
  --kaniko-image=<image>   Kaniko executor image for building [default: gcr.io/kaniko-project/executor:latest].
  --push, -p               Push the built images to a registry.
  --deploy, -d             Deploy the images after building.
  --dry-run, --dry         Dry run mode: build images without pushing, with cleanup.
  --version, -v            Show script version.
  --help, -h               Show documentation.
"""

import os
import sys
import yaml
import subprocess
import typing as t
import logging
from dotenv import load_dotenv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from kaniko.helpers.castom_exeption import FailedBuild
from kaniko.helpers.logger_file import LoggerEngine

SCRIPT_VERSION = "1.1.0.0"

# Initialize logging
logger_engine = LoggerEngine("KanikoBuilder", logging.INFO)
logger = logger_engine.logger

# Load environment variables from .env file
load_dotenv()


def builder(opts: t.Dict[str, t.Any]):
    compose_file = opts["--compose-file"]
    kaniko_image = opts["--kaniko-image"]
    push = opts["--push"] or opts["--deploy"]
    dry_run = opts["--dry-run"]

    compose_data = load_compose_file(compose_file)
    services = compose_data.get("services", {})
    image_names = defaultdict(int)

    for service_name, service_data in services.items():
        image_name = service_data.get("image")
        if image_name:
            image_names[image_name] += 1
        else:
            logger.warning(f"No image specified for service {service_name}")

    for image_name, count in image_names.items():
        if count > 1:
            logger.error(f"Image name '{image_name}' is used {count} times.")
            sys.exit(1)

    with ThreadPoolExecutor() as executor:
        futures = []
        for service_name, service_data in services.items():
            build_data = service_data.get("build", {})
            build_context = build_data.get("context", ".")
            dockerfile = build_data.get("dockerfile", "Dockerfile")
            image_name = service_data.get("image")
            build_args = build_data.get("args", {})

            build_args = {
                key: os.getenv(key, value) for key, value in build_args.items()
            }

            if image_name:
                futures.append(
                    executor.submit(
                        build_with_kaniko,
                        service_name,
                        build_context,
                        dockerfile,
                        image_name,
                        build_args,
                        kaniko_image,
                        push,
                        dry_run,
                    )
                )

        for future in as_completed(futures):
            try:
                future.result()
            except FailedBuild as e:
                logger.error(f"Build failed: {e}")
                sys.exit(1)


def load_compose_file(file_path: str):
    """Load docker-compose file."""
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"File {file_path} not found.")
        sys.exit(1)
    except yaml.YAMLError as y:
        logger.error(f"Error parsing yaml: {y}")
        sys.exit(1)


def build_with_kaniko(
    service_name,
    build_context,
    dockerfile,
    image_name,
    build_args,
    kaniko_image,
    push,
    dry_run,
):
    kaniko_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{os.path.abspath(build_context)}:/workspace",
    ]

    kaniko_command.extend(
        [
            "-v",
            f'{os.path.expanduser("~")}/.docker:/kaniko/.docker:ro',
            kaniko_image,
            "--context",
            "/workspace",
            "--dockerfile",
            f"/workspace/{dockerfile}",
            "--snapshot-mode=redo",
            "--cache=false",
        ]
    )

    if push:
        kaniko_command.extend(["--destination", image_name])
    elif dry_run:
        kaniko_command.append("--no-push")

    for arg_name, arg_value in build_args.items():
        kaniko_command.extend(["--build-arg", f"{arg_name}={arg_value}"])

    logger.info(f"Building {service_name} with Kaniko: {' '.join(kaniko_command)}")

    process = subprocess.Popen(
        kaniko_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    for line in process.stdout:
        logger.info(line.strip())

    process.wait()

    if process.returncode != 0:
        for line in process.stderr:
            logger.error(line.strip())
        logger.error(f"Error building {service_name}")
        raise FailedBuild(f"Failed to build {service_name}")
    else:
        logger.info(f"Successfully built {service_name}")
