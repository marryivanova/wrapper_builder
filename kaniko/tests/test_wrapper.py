import subprocess
import unittest
from unittest.mock import mock_open, patch

from kaniko.commands.build.cmd import run_build
from kaniko.commands.build.kaniko.kaniko_wrapper import load_compose_file


class TestKanikoWrapper(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_build_success(self, mock_run):
        mock_run.return_value = None

        opts = {
            "compose_file": "docker-compose.yml",
            "kaniko_image": "gcr.io/kaniko-project/executor:latest",
            "push": True,
            "deploy": False,
            "dry_run": False,
        }
        logger = unittest.mock.MagicMock()
        run_build(opts, logger)

        mock_run.assert_called_once_with(
            [
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
            ],
            check=True,
        )

    @patch("subprocess.run")
    def test_run_build_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker run")

        opts = {
            "compose_file": "docker-compose.yml",
            "kaniko_image": "gcr.io/kaniko-project/executor:latest",
            "push": True,
            "deploy": False,
            "dry_run": False,
        }
        logger = unittest.mock.MagicMock()
        run_build(opts, logger)

        logger.error.assert_called_with(
            "❌ Kaniko build failed with error: Command 'docker run' returned non-zero exit status 1."
        )


class TestLoadComposeFile(unittest.TestCase):
    def setUp(self):
        self.compose_file_path = "path/to/docker-compose.yml"
        self.invalid_compose_file_path = "path/to/invalid-docker-compose.yml"
        self.valid_yaml_content = """
        version: '3'
        services:
          web:
            image: nginx
        """
        self.invalid_yaml_content = """
        invalid content
        """

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="version: '3'\nservices:\n  web:\n    image: nginx",
    )
    def test_valid_file(self, mock_file):
        result = load_compose_file(self.compose_file_path)

        self.assertIsNotNone(result)
        self.assertIn("version", result)
        self.assertIn("services", result)
        mock_file.assert_called_once_with(self.compose_file_path, "r")

    @patch("builtins.open", new_callable=mock_open)
    def test_file_not_found(self, mock_file):
        mock_file.side_effect = FileNotFoundError

        with self.assertRaises(FileNotFoundError) as context:
            load_compose_file(self.compose_file_path)

        self.assertTrue(
            f"File not found: {self.compose_file_path}" in str(context.exception)
        )
