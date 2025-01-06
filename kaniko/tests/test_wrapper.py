import os
import unittest

from kaniko.commands.build.cmd import CommandLineOptions
from kaniko.commands.build.kaniko.kaniko_wrapper import KanikoCommandBuilder


class TestKanikoCommandBuilder(unittest.TestCase):
    def setUp(self):
        self.kaniko_image = "gcr.io/kaniko-project/executor:latest"
        self.builder = KanikoCommandBuilder(self.kaniko_image)

    def test_build_command_with_push(self):
        context = "path/to/context"
        dockerfile = "Dockerfile"
        image = "my-image:latest"
        build_args = {"ARG1": "value1", "ARG2": "value2"}
        push = True

        expected_command = [
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
            "--destination",
            image,
        ] + ["--build-arg", "ARG1=value1", "--build-arg", "ARG2=value2"]

        command = self.builder.build_command(
            context, dockerfile, image, build_args, push
        )
        self.assertEqual(command, expected_command)

    def test_build_command_without_push(self):
        context = "path/to/context"
        dockerfile = "Dockerfile"
        image = "my-image:latest"
        build_args = {"ARG1": "value1", "ARG2": "value2"}
        push = False

        expected_command = [
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
            "--no-push",
        ] + ["--build-arg", "ARG1=value1", "--build-arg", "ARG2=value2"]

        command = self.builder.build_command(
            context, dockerfile, image, build_args, push
        )
        self.assertEqual(command, expected_command)

    def test_build_command_with_no_build_args(self):
        context = "path/to/context"
        dockerfile = "Dockerfile"
        image = "my-image:latest"
        build_args = {}
        push = True

        expected_command = [
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
            "--destination",
            image,
        ]

        command = self.builder.build_command(
            context, dockerfile, image, build_args, push
        )
        self.assertEqual(command, expected_command)


class TestCommandLineOptions(unittest.TestCase):

    def test_default_initialization(self):
        options = CommandLineOptions()
        self.assertEqual(options.compose_file, "docker-compose.yml")
        self.assertEqual(options.kaniko_image, "gcr.io/kaniko-project/executor:latest")
        self.assertFalse(options.push)
        self.assertFalse(options.deploy)
        self.assertFalse(options.dry_run)
        self.assertFalse(options.version)

    def test_custom_initialization(self):
        custom_options = {
            "--compose-file": "custom-compose.yml",
            "--kaniko-image": "my-kaniko-image",
            "--push": True,
            "--deploy": True,
            "--dry-run": True,
            "--version": True,
        }
        options = CommandLineOptions.from_dict(custom_options)
        self.assertEqual(options.compose_file, "custom-compose.yml")
        self.assertEqual(options.kaniko_image, "my-kaniko-image")
        self.assertTrue(options.push)
        self.assertTrue(options.deploy)
        self.assertTrue(options.dry_run)
        self.assertTrue(options.version)

    def test_validation(self):
        options = CommandLineOptions()
        self.assertTrue(options.validate())

        options.compose_file = ""
        self.assertFalse(options.validate())

        options.compose_file = "docker-compose.yml"
        options.kaniko_image = ""
        self.assertFalse(options.validate())
