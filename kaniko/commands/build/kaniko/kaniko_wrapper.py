import os
import yaml
import subprocess
import typing as t
from concurrent.futures import ThreadPoolExecutor, as_completed
from kaniko.helpers.logger_file import _init_log

logger = _init_log()


class DockerComposeLoader:

    def __init__(self, compose_file: str):
        self.compose_file = compose_file

    def load(self) -> t.Dict[str, t.Dict]:
        """
        Load and validate the Docker Compose file.

        This method attempts to load the specified Docker Compose file and extract
        the 'services' section. If the file doesn't exist, it raises a FileNotFoundError.

        Args:
            self: The instance of the DockerComposeLoader class.

        Returns:
            t.Dict[str, t.Dict]: A dictionary containing the 'services' section of the
            Docker Compose file. If no 'services' section is found, it returns an empty dictionary.

        Raises:
            FileNotFoundError: If the specified Docker Compose file does not exist.
        """
        if not os.path.exists(self.compose_file):
            logger.error(f"Compose file not found: {self.compose_file}")
            raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

        logger.info(f"Loading compose file: {self.compose_file}")
        with open(self.compose_file, "r") as file:
            data = yaml.safe_load(file)
            return data.get("services", {})


class KanikoCommandBuilder:
    def __init__(self, kaniko_image: str):
        self.kaniko_image = kaniko_image

    def build_command(
        self,
        context: str,
        dockerfile: str,
        image: str,
        build_args: t.Dict[str, str],
        push: bool,
    ) -> t.List[str]:
        """
        Build a Kaniko command for building and optionally pushing a Docker image.

        This method constructs a command list that can be used to run Kaniko
        for building a Docker image based on the provided parameters.

        Args:
            context (str): The build context path.
            dockerfile (str): The path to the Dockerfile relative to the context.
            image (str): The name and tag of the image to be built.
            build_args (t.Dict[str, str]): A dictionary of build arguments to be passed to the build process.
            push (bool): Whether to push the built image to a registry.

        Returns:
            t.List[str]: A list of strings representing the Kaniko command to be executed.
        """
        command = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{os.path.abspath(context)}:/workspace",
            "-v",
            f"{os.path.expanduser('~')}/.docker:/kaniko/.docker:ro",
            self.kaniko_image,
            "--context",
            "/workspace",
            "--dockerfile",
            f"/workspace/{dockerfile}",
            "--snapshot-mode=redo",
            "--cache=false",
            "--cleanup",
        ]
        if push:
            command.extend(["--destination", image])
        else:
            command.append("--no-push")

        for arg, value in build_args.items():
            command.extend(["--build-arg", f"{arg}={value}"])

        return command


class KanikoExecutor:

    def __init__(self, kaniko_image: str, push: bool, dry_run: bool):
        """
        Initialize the KanikoExecutor.

        Args:
            kaniko_image (str): The Kaniko executor image to use.
            push (bool): Whether to push the built image to a registry.
            dry_run (bool): If True, only log the command without executing it.
        """
        self.kaniko_image = kaniko_image
        self.push = push
        self.dry_run = dry_run

    def run_build(
        self,
        service_name: str,
        context: str,
        dockerfile: str,
        image: str,
        build_args: t.Dict[str, str],
    ):
        """
        Execute a Kaniko build for a given service.

        This method builds a Docker image using Kaniko based on the provided parameters.
        If dry_run is True, it only logs the command without executing it.

        Args:
            service_name (str): The name of the service being built.
            context (str): The build context path.
            dockerfile (str): The path to the Dockerfile relative to the context.
            image (str): The name and tag of the image to be built.
            build_args (t.Dict[str, str]): A dictionary of build arguments to be passed to the build process.

        Raises:
            subprocess.CalledProcessError: If the Kaniko build process fails.

        Returns:
            None
        """
        command_builder = KanikoCommandBuilder(self.kaniko_image)
        command = command_builder.build_command(
            service_name, context, dockerfile, image, build_args, self.push
        )

        if self.dry_run:
            logger.info(
                f"[Dry-Run] Command for service {service_name}: {' '.join(command)}"
            )
            return

        try:
            logger.info(f"Building service: {service_name}")
            subprocess.run(command, check=True)
            logger.info(f"Service {service_name} built successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to build service {service_name}: {e}")
            raise


class KanikoBuilder:
    """
    A class for building Docker images using Kaniko based on a Docker Compose file.
    """

    def __init__(self, compose_file: str, kaniko_image: str, push: bool, dry_run: bool):
        """
        Initialize the KanikoBuilder.

        Args:
            compose_file (str): Path to the Docker Compose file.
            kaniko_image (str): The Kaniko executor image to use for building.
            push (bool): Whether to push the built images to a registry.
            dry_run (bool): If True, only log the commands without executing them.
        """
        self.compose_file = compose_file
        self.kaniko_image = kaniko_image
        self.push = push
        self.dry_run = dry_run

    def execute(self):
        """
        Execute the Kaniko build process for all services defined in the Docker Compose file.

        This method loads the services from the Docker Compose file, creates a KanikoExecutor,
        and uses a ThreadPoolExecutor to build all services concurrently.

        Raises:
            Exception: If any error occurs during the build process for any service.

        Returns:
            None
        """
        loader = DockerComposeLoader(self.compose_file)
        services = loader.load()
        executor = KanikoExecutor(self.kaniko_image, self.push, self.dry_run)

        with ThreadPoolExecutor() as pool:
            tasks = [
                pool.submit(
                    executor.run_build,
                    service_name,
                    service.get("build", {}).get("context", "."),
                    service.get("build", {}).get("dockerfile", "Dockerfile"),
                    service["image"],
                    service.get("build", {}).get("args", {}),
                )
                for service_name, service in services.items()
                if "image" in service
            ]

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error during build for service: {e}")
                    raise
