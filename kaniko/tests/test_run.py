import subprocess
import unittest
from unittest.mock import MagicMock, patch

from kaniko.commands.build.cmd import (
    KanikoBuildCommand,
    LoggerModel,
    CommandLineOptions,
)


class TestKanikoBuildCommand(unittest.TestCase):
    def setUp(self):
        self.mock_opts = MagicMock(spec=CommandLineOptions)
        self.mock_opts.compose_file = "docker-compose.yml"
        self.mock_opts.kaniko_image = "gcr.io/kaniko-project/executor:latest"
        self.mock_opts.push = False
        self.mock_opts.deploy = False
        self.mock_opts.dry_run = False

        self.build_command = KanikoBuildCommand(self.mock_opts)
        self.mock_logger = MagicMock(spec=LoggerModel)

    def test_build_command_basic(self):
        self.mock_opts.push = False
        self.mock_opts.deploy = False

        expected_command = [
            "docker",
            "run",
            "--rm",
            "-v",
            "docker-compose.yml:/workspace",
            "gcr.io/kaniko-project/executor:latest",
            "--context",
            "/workspace",
            "--dockerfile",
            "/workspace/Dockerfile",
        ]
        self.assertEqual(self.build_command.build_command(), expected_command)

    def test_build_command_with_push(self):
        self.mock_opts.push = True
        self.mock_opts.deploy = False
        expected_command = [
            "docker",
            "run",
            "--rm",
            "-v",
            "docker-compose.yml:/workspace",
            "gcr.io/kaniko-project/executor:latest",
            "--context",
            "/workspace",
            "--dockerfile",
            "/workspace/Dockerfile",
            "--destination",
            "your-registry/your-image:latest",
        ]
        self.assertEqual(self.build_command.build_command(), expected_command)

    def test_run_build_error_logging(self):
        self.mock_opts.dry_run = False
        mock_subprocess_run = MagicMock(
            side_effect=subprocess.CalledProcessError(1, "test")
        )

        with patch("subprocess.run", mock_subprocess_run):
            self.build_command.run_build(self.mock_logger)

        self.mock_logger.log_error.assert_called_once_with(
            "❌ Kaniko build failed with error: Command 'test' returned non-zero exit status 1."
        )

    def test_build_command_with_deploy(self):
        self.mock_opts.push = False
        self.mock_opts.deploy = True

        expected_command = [
            "docker",
            "run",
            "--rm",
            "-v",
            "docker-compose.yml:/workspace",
            "gcr.io/kaniko-project/executor:latest",
            "--context",
            "/workspace",
            "--dockerfile",
            "/workspace/Dockerfile",
            "--destination",
            "your-registry/your-image:latest",
            "--deploy",
        ]
        self.assertEqual(self.build_command.build_command(), expected_command)

    def test_run_build_dry_run(self):
        self.mock_opts.dry_run = True
        build_command = KanikoBuildCommand(self.mock_opts)
        build_command.run_build(self.mock_logger)

        self.mock_logger.log_info.assert_called_once_with(
            "🔍 Running in dry-run mode. No images will be pushed."
        )
        self.mock_logger.log_error.assert_not_called()

    def test_build_command_with_required_options(self):
        self.mock_opts.compose_file = "test-compose.yml"
        self.mock_opts.kaniko_image = "test-kaniko-image:latest"
        self.mock_opts.push = False
        self.mock_opts.deploy = False

        expected_command = [
            "docker",
            "run",
            "--rm",
            "-v",
            "test-compose.yml:/workspace",
            "test-kaniko-image:latest",
            "--context",
            "/workspace",
            "--dockerfile",
            "/workspace/Dockerfile",
        ]

        self.assertEqual(self.build_command.build_command(), expected_command)
