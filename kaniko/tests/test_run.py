import logging
import unittest
from unittest.mock import patch

from kaniko.commands.build.cmd import run_build, parse_options


class TestKanikoBuild(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_build(self, mock_run):
        opts = {
            "compose_file": "docker-compose.yml",
            "kaniko_image": "gcr.io/kaniko-project/executor:latest",
            "push": True,
            "deploy": False,
            "dry_run": False,
            "version": False,
        }

        mock_run.return_value = None
        run_build(opts, logging.getLogger("test"))
        mock_run.assert_called_once()


class TestKanikoScript(unittest.TestCase):
    def test_parse_options(self):
        opts = {
            "--compose-file": "docker-compose.yml",
            "--kaniko-image": "gcr.io/kaniko-project/executor:latest",
            "--push": True,
            "--deploy": False,
            "--dry-run": False,
            "--version": False,
        }

        parsed_options = parse_options(opts)

        self.assertEqual(parsed_options["compose_file"], "docker-compose.yml")
        self.assertEqual(
            parsed_options["kaniko_image"], "gcr.io/kaniko-project/executor:latest"
        )
        self.assertTrue(parsed_options["push"])
        self.assertFalse(parsed_options["deploy"])
        self.assertFalse(parsed_options["dry_run"])
        self.assertFalse(parsed_options["version"])

    def test_parse_options_with_default_values(self):
        opts = {
            "--kaniko-image": "gcr.io/kaniko-project/executor:latest",
            "--push": False,
            "--deploy": False,
            "--dry-run": False,
            "--version": False,
        }

        parsed_options = parse_options(opts)

        self.assertEqual(parsed_options["compose_file"], "docker-compose.yml")
        self.assertEqual(
            parsed_options["kaniko_image"], "gcr.io/kaniko-project/executor:latest"
        )
        self.assertFalse(parsed_options["push"])
        self.assertFalse(parsed_options["deploy"])
        self.assertFalse(parsed_options["dry_run"])
        self.assertFalse(parsed_options["version"])

    def test_invalid_options(self):
        opts = {
            "--invalid-option": "invalid_value",
        }

        parsed_options = parse_options(opts)
        self.assertNotIn("invalid_option", parsed_options)
