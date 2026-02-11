"""Tests for CLI interface."""

from unittest.mock import MagicMock, patch

import pytest

from build_mpq.cli import cmd_create, cmd_package, cmd_validate, main


class TestCLICreate:
    """Tests for the create command."""

    @patch("build_mpq.cli.create_staging_area")
    def test_cmd_create_success(self, mock_create: MagicMock):
        """Test successful create command."""
        args = MagicMock(path="/tmp/staging", force=False)

        result = cmd_create(args)

        assert result == 0
        mock_create.assert_called_once()

    @patch("build_mpq.cli.create_staging_area")
    def test_cmd_create_handles_file_exists_error(
        self, mock_create: MagicMock, capsys
    ):
        """Test create command handles FileExistsError."""
        mock_create.side_effect = FileExistsError("already exists")
        args = MagicMock(path="/tmp/staging", force=False)

        result = cmd_create(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "already exists" in captured.err


class TestCLIPackage:
    """Tests for the package command."""

    @patch("build_mpq.cli.package_mpq")
    def test_cmd_package_success(self, mock_package: MagicMock):
        """Test successful package command."""
        args = MagicMock(
            staging="/tmp/staging",
            output="/tmp/output.mpq",
            compression="z",
        )

        result = cmd_package(args)

        assert result == 0
        mock_package.assert_called_once()

    @patch("build_mpq.cli.package_mpq")
    def test_cmd_package_handles_file_not_found(
        self, mock_package: MagicMock, capsys
    ):
        """Test package command handles FileNotFoundError."""
        mock_package.side_effect = FileNotFoundError("not found")
        args = MagicMock(
            staging="/tmp/staging",
            output="/tmp/output.mpq",
            compression="z",
        )

        result = cmd_package(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


class TestCLIValidate:
    """Tests for the validate command."""

    @patch("build_mpq.cli.validate_mpq")
    def test_cmd_validate_success(self, mock_validate: MagicMock):
        """Test successful validate command."""
        args = MagicMock(mpq="/tmp/test.mpq", verbose=False)

        result = cmd_validate(args)

        assert result == 0
        mock_validate.assert_called_once()

    @patch("build_mpq.cli.validate_mpq")
    def test_cmd_validate_handles_validation_error(
        self, mock_validate: MagicMock, capsys
    ):
        """Test validate command handles ValidationError."""
        from build_mpq.operations import ValidationError

        mock_validate.side_effect = ValidationError("invalid")
        args = MagicMock(mpq="/tmp/test.mpq", verbose=False)

        result = cmd_validate(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Validation failed" in captured.err


class TestMainCLI:
    """Tests for main CLI entry point."""

    def test_main_requires_command(self):
        """Test that main requires a command."""
        with patch("sys.argv", ["build-mpq"]):
            with pytest.raises(SystemExit):
                main()

    @patch("sys.argv", ["build-mpq", "--version"])
    def test_main_version(self):
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch("sys.argv", ["build-mpq", "create", "--help"])
    def test_main_create_help(self):
        """Test create --help."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch("build_mpq.cli.create_staging_area")
    @patch("sys.argv", ["build-mpq", "create", "/tmp/staging"])
    def test_main_create_command(self, mock_create: MagicMock):
        """Test running create command through main."""
        result = main()

        assert result == 0
        mock_create.assert_called_once()

    @patch("build_mpq.cli.package_mpq")
    @patch("sys.argv", ["build-mpq", "package", "/tmp/staging", "/tmp/out.mpq"])
    def test_main_package_command(self, mock_package: MagicMock):
        """Test running package command through main."""
        result = main()

        assert result == 0
        mock_package.assert_called_once()

    @patch("build_mpq.cli.validate_mpq")
    @patch("sys.argv", ["build-mpq", "validate", "/tmp/test.mpq"])
    def test_main_validate_command(self, mock_validate: MagicMock):
        """Test running validate command through main."""
        result = main()

        assert result == 0
        mock_validate.assert_called_once()
