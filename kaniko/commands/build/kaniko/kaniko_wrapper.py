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

SCRIPT_VERSION = "1.1.0.0"

load_dotenv()

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("KanikoBuilder")


def load_compose_file(file_path: str) -> t.Dict:
    """Load and return the docker-compose file as a dictionary."""
    try:
        logger.info(f"Loading docker-compose file: {file_path}")
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(
            f"File not found: {file_path}. Please check the path and try again."
        )
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {file_path}: {e}")
        sys.exit(1)


def build_with_kaniko(
    service_name: str,
    build_context: str,
    dockerfile: str,
    image_name: str,
    build_args: t.Dict,
    kaniko_image: str,
    deploy: bool,
    dry: bool,
):
    """Build the image using Kaniko."""
    logger.info(f"Starting build for service: {service_name}")
    logger.debug(f"Build context: {build_context}, Dockerfile: {dockerfile}")

    # Construct Kaniko command
    kaniko_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{os.path.abspath(build_context)}:/workspace",
        "-v",
        f'{os.path.expanduser("~")}/.docker:/kaniko/.docker:ro',
        kaniko_image,
        "--context",
        "/workspace",
        "--dockerfile",
        f"/workspace/{dockerfile}",
        "--snapshot-mode=redo",
        "--cache=false",
        "--cleanup",
    ]

    if deploy:
        kaniko_command.extend(["--destination", image_name])
    elif dry:
        kaniko_command.append("--no-push")

    for arg_name, arg_value in build_args.items():
        kaniko_command.extend(["--build-arg", f"{arg_name}={arg_value}"])

    logger.debug(f"Kaniko command: {' '.join(kaniko_command)}")

    try:
        process = subprocess.Popen(
            kaniko_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Log output
        for line in process.stdout:
            logger.info(f"[Kaniko] {line.strip()}")

        process.wait()

        if process.returncode == 0:
            logger.info(f"Successfully built service: {service_name}")
        else:
            for line in process.stderr:
                logger.error(f"[Kaniko Error] {line.strip()}")
            raise FailedBuild(f"Failed to build service: {service_name}")
    except Exception as e:
        logger.error(f"Unexpected error while building {service_name}: {e}")
        raise


def builder(opts: t.Dict[str, t.Any]):
    """Main build function."""
    compose_file = opts.get("--compose-file", "docker-compose.yml")
    kaniko_image = opts.get("--kaniko-image", "gcr.io/kaniko-project/executor:latest")
    deploy = opts.get("--push") or opts.get("--deploy")
    dry = opts.get("--dry-run", False)

    logger.info("Starting Kaniko build process...")
    logger.debug(f"Options: {opts}")

    # Load the docker-compose file
    compose_data = load_compose_file(compose_file)
    services = compose_data.get("services", {})

    # Check for duplicate image names
    image_names = defaultdict(int)
    for service_name, service_data in services.items():
        image_name = service_data.get("image")
        if image_name:
            image_names[image_name] += 1
        else:
            logger.warning(f"Service '{service_name}' does not specify an image.")

    for image_name, count in image_names.items():
        if count > 1:
            logger.error(
                f"Duplicate image name detected: {image_name} used {count} times."
            )
            sys.exit(1)

    try:
        # Build images in parallel
        with ThreadPoolExecutor() as executor:
            tasks = [
                executor.submit(
                    build_with_kaniko,
                    service_name,
                    service_data.get("build", {}).get("context", "."),
                    service_data.get("build", {}).get("dockerfile", "Dockerfile"),
                    image_name,
                    {
                        key: os.getenv(key, value)
                        for key, value in service_data.get("build", {})
                        .get("args", {})
                        .items()
                    },
                    kaniko_image,
                    deploy,
                    dry,
                )
                for service_name, service_data in services.items()
                if (image_name := service_data.get("image"))
            ]

            # Wait for all builds to finish
            for future in as_completed(tasks):
                future.result()

    except FailedBuild as exc:
        logger.error(f"Build process failed: {exc}")
        sys.exit(1)
    except Exception as exc:
        logger.critical(f"An unexpected error occurred: {exc}")
        sys.exit(1)
