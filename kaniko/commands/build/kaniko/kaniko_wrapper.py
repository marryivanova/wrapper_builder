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
            logger.info(f"Executing command: {' '.join(command)}")
            subprocess.run(command, check=True)
            logger.info(f"Service {service_name} built successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to build service {service_name}: {e}")
            raise


class KanikoBuilder:
    def __init__(self, compose_file: str, kaniko_image: str, push: bool, dry_run: bool):
        self.compose_file = compose_file
        self.kaniko_image = kaniko_image
        self.push = push
        self.dry_run = dry_run

    def execute(self):
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
