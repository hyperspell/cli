"""Basic CLI tests - help output, command registration, config loading."""

from __future__ import annotations

import json
import sys
from unittest.mock import patch

from typer.testing import CliRunner

# Mock the hyperspell SDK before importing our code
sys.modules.setdefault("hyperspell", type(sys)("hyperspell"))

from hyperspell_cli.config import (  # noqa: E402
    DEFAULT_BASE_URL,
    clear_config,
    load_config,
    save_config,
)
from hyperspell_cli.main import app  # noqa: E402

runner = CliRunner()


class TestHelpOutput:
    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Hyperspell CLI" in result.output

    def test_auth_help(self):
        result = runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output
        assert "whoami" in result.output

    def test_memories_help(self):
        result = runner.invoke(app, ["memories", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "add" in result.output
        assert "delete" in result.output

    def test_search_help(self):
        result = runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "query" in result.output.lower() or "QUERY" in result.output

    def test_connections_help(self):
        result = runner.invoke(app, ["connections", "--help"])
        assert result.exit_code == 0

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "hyperspell-cli" in result.output


class TestCommandRegistration:
    def test_top_level_commands(self):
        result = runner.invoke(app, ["--help"])
        for cmd in ["auth", "memories", "connections", "search"]:
            assert cmd in result.output, f"Missing top-level command: {cmd}"

    def test_auth_subcommands(self):
        result = runner.invoke(app, ["auth", "--help"])
        for cmd in ["login", "logout", "status", "whoami"]:
            assert cmd in result.output, f"Missing auth subcommand: {cmd}"

    def test_memories_subcommands(self):
        result = runner.invoke(app, ["memories", "--help"])
        for cmd in ["list", "add", "get", "delete", "status"]:
            assert cmd in result.output, f"Missing memories subcommand: {cmd}"


class TestConfig:
    def test_load_config_missing_file(self, tmp_path):
        with patch("hyperspell_cli.config.CONFIG_PATH", tmp_path / "nonexistent.json"):
            assert load_config() == {}

    def test_save_and_load_config(self, tmp_path):
        config_path = tmp_path / "config.json"
        with (
            patch("hyperspell_cli.config.CONFIG_PATH", config_path),
            patch("hyperspell_cli.config.CONFIG_DIR", tmp_path),
        ):
            save_config({"api_key": "test-key", "base_url": "https://example.com"})
            cfg = load_config()
            assert cfg["api_key"] == "test-key"
            assert cfg["base_url"] == "https://example.com"

    def test_clear_config(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text("{}")
        with patch("hyperspell_cli.config.CONFIG_PATH", config_path):
            clear_config()
            assert not config_path.exists()

    def test_load_config_invalid_json(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text("not json")
        with patch("hyperspell_cli.config.CONFIG_PATH", config_path):
            assert load_config() == {}

    def test_default_base_url(self):
        assert DEFAULT_BASE_URL == "https://api.hyperspell.com"


class TestLogoutYesFlag:
    def test_logout_requires_confirmation_noninteractive(self):
        result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code != 0

    def test_logout_yes_flag_skips_confirmation(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"api_key": "test"}))
        with (
            patch("hyperspell_cli.config.CONFIG_PATH", config_path),
            patch("hyperspell_cli.commands.auth.clear_config") as mock_clear,
        ):
            runner.invoke(app, ["auth", "logout", "--yes"])
            mock_clear.assert_called_once()


class TestDeleteYesFlag:
    def test_delete_requires_confirmation_noninteractive(self):
        result = runner.invoke(app, ["memories", "delete", "test-source", "test-id"])
        assert result.exit_code != 0

    def test_delete_yes_flag(self):
        with patch("hyperspell_cli.commands.memories.get_sdk_client") as mock_client:
            mock_client.return_value.memories.delete.return_value = None
            runner.invoke(app, ["memories", "delete", "src", "rid", "--yes"])
            mock_client.assert_called()


class TestWhoami:
    def test_whoami_json(self):
        import httpx

        mock_response = httpx.Response(
            200,
            json={"email": "test@example.com", "name": "Test User"},
            request=httpx.Request("GET", "https://api.hyperspell.com/auth/me"),
        )

        with patch("hyperspell_cli.commands.auth.get_http_client") as mock_http:
            mock_http.return_value.get.return_value = mock_response
            result = runner.invoke(app, ["--json", "auth", "whoami"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["email"] == "test@example.com"
