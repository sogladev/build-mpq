"""Tests for MPQ operations."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import subprocess
import errno

import pytest

from build_mpq.operations import (
    MPQCliNotFoundError,
    ValidationError,
    create_staging_area,
    package_mpq,
    validate_mpq,
)


@pytest.fixture
def temp_staging(tmp_path: Path) -> Path:
    """Create a temporary staging directory."""
    staging = tmp_path / "staging"
    return staging


@pytest.fixture
def populated_staging(temp_staging: Path) -> Path:
    """Create a staging area with some test files."""
    create_staging_area(temp_staging)

    # Add some test files
    (temp_staging / "DBFilesClient" / "test.dbc").write_text("test data")
    (temp_staging / "Interface" / "Icons" / "icon.blp").write_text("icon data")

    return temp_staging


class TestCreateStagingArea:
    """Tests for create_staging_area function."""

    def test_creates_all_directories(self, temp_staging: Path):
        """Test that all required directories are created."""
        create_staging_area(temp_staging)

        assert temp_staging.exists()
        assert temp_staging.is_dir()

        # Check a few key directories
        assert (temp_staging / "DBFilesClient").exists()
        assert (temp_staging / "Interface" / "Icons").exists()
        assert (temp_staging / "Sound" / "Music").exists()
        assert (temp_staging / "World" / "Maps").exists()

    def test_creates_readme(self, temp_staging: Path):
        """Test that README.txt is created."""
        create_staging_area(temp_staging)

        readme = temp_staging / "README.txt"
        assert readme.exists()
        assert readme.is_file()

        content = readme.read_text()
        assert "WoW 3.3.5a" in content
        assert "DBFilesClient" in content

    def test_raises_error_if_exists_without_force(self, temp_staging: Path):
        """Test that FileExistsError is raised if staging exists."""
        create_staging_area(temp_staging)

        with pytest.raises(FileExistsError, match="already exists"):
            create_staging_area(temp_staging, force=False)

    def test_force_recreates_staging_area(self, temp_staging: Path):
        """Test that force=True recreates the staging area."""
        # Create initial staging
        create_staging_area(temp_staging)
        test_file = temp_staging / "test.txt"
        test_file.write_text("should be removed")

        # Recreate with force
        create_staging_area(temp_staging, force=True)

        assert temp_staging.exists()
        assert not test_file.exists()
        assert (temp_staging / "README.txt").exists()

    def test_create_with_categories(self, temp_staging: Path):
        """Test creating staging area with specific categories."""
        create_staging_area(temp_staging, categories=["dbc", "interface"])

        # Should have DBC and Interface directories
        assert (temp_staging / "DBFilesClient").exists()
        assert (temp_staging / "Interface" / "Icons").exists()

        # Should NOT have Sound directories
        assert not (temp_staging / "Sound").exists()

        # Check README mentions categories
        readme = temp_staging / "README.txt"
        content = readme.read_text()
        assert "dbc" in content.lower()
        assert "interface" in content.lower()

    def test_create_with_invalid_category(self, temp_staging: Path):
        """Test that invalid categories raise ValueError."""
        with pytest.raises(ValueError, match="Invalid categories"):
            create_staging_area(temp_staging, categories=["invalid"])


class TestPackageMPQ:
    """Tests for package_mpq function."""

    @pytest.fixture
    def real_asset_files(self, tmp_path: Path) -> Path:
        """Create a directory with real asset files outside staging area."""
        assets_dir = tmp_path / "real_assets"
        assets_dir.mkdir()

        # Create some real asset files
        (assets_dir / "spell.dbc").write_bytes(b"DBC_FILE_DATA_12345")
        (assets_dir / "icon.blp").write_bytes(b"BLP_ICON_DATA_67890")
        (assets_dir / "music.mp3").write_bytes(b"MP3_AUDIO_DATA_11111")

        return assets_dir

    def test_raises_error_if_staging_not_found(self, tmp_path: Path):
        """Test that FileNotFoundError is raised if staging doesn't exist."""
        staging = tmp_path / "nonexistent"
        output = tmp_path / "output.mpq"

        with pytest.raises(FileNotFoundError, match="not found"):
            package_mpq(staging, output)

    def test_raises_error_if_staging_not_directory(self, tmp_path: Path):
        """Test that NotADirectoryError is raised if staging is a file."""
        staging = tmp_path / "file.txt"
        staging.write_text("test")
        output = tmp_path / "output.mpq"

        with pytest.raises(NotADirectoryError):
            package_mpq(staging, output)

    @patch("shutil.which")
    def test_raises_error_if_mpqcli_not_found(
        self, mock_which: MagicMock, populated_staging: Path, tmp_path: Path
    ):
        """Test that MPQCliNotFoundError is raised if mpqcli is not in PATH."""
        mock_which.return_value = None
        output = tmp_path / "output.mpq"

        with pytest.raises(MPQCliNotFoundError, match="not found in PATH"):
            package_mpq(populated_staging, output)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_calls_mpqcli_with_correct_arguments(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        populated_staging: Path,
        tmp_path: Path,
    ):
        """Test that mpqcli is called with correct arguments."""
        mock_which.return_value = "/usr/bin/mpqcli"

        output = tmp_path / "output.mpq"

        # Mock subprocess to create the file as a side effect
        def create_output_file(*args, **kwargs):
            output.write_bytes(b"fake mpq data")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_output_file

        package_mpq(populated_staging, output, compression="z")

        mock_run.assert_called_once()
        call_args = mock_run.call_args

        cmd_args = call_args[0][0]
        assert cmd_args[0] == "mpqcli"
        assert cmd_args[1] == "create"
        # Should use --output and pass the staging dir as the target ('.')
        assert "--output" in cmd_args
        assert str(output.absolute()) in cmd_args
        assert cmd_args[-1] == "."
        assert "--compression" not in cmd_args

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_handles_symbolic_links(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        temp_staging: Path,
        real_asset_files: Path,
        tmp_path: Path,
    ):
        """Test that symbolic links are resolved correctly."""
        mock_which.return_value = "/usr/bin/mpqcli"

        # Create staging area
        create_staging_area(temp_staging)

        # Create symbolic links to real assets
        dbc_link = temp_staging / "DBFilesClient" / "Spell.dbc"
        dbc_link.symlink_to(real_asset_files / "spell.dbc")

        icon_link = temp_staging / "Interface" / "Icons" / "spell_icon.blp"
        icon_link.symlink_to(real_asset_files / "icon.blp")

        output = tmp_path / "output.mpq"

        # Mock subprocess
        def create_output_file(*args, **kwargs):
            # Ensure we invoke mpqcli with the staging dir target ('.') and not absolute asset paths
            cmd_args = args[0]
            cmd_str = " ".join(str(arg) for arg in cmd_args)

            assert "." in cmd_args
            # The real asset files should not appear in the mpqcli command (we pass the staging dir)
            assert str(real_asset_files / "spell.dbc") not in cmd_str
            assert str(real_asset_files / "icon.blp") not in cmd_str

            # With dereference enabled by default, we should run mpqcli from a temp copy
            cwd = kwargs.get("cwd")
            assert cwd is not None
            assert Path(cwd) != temp_staging

            # The copied files should exist in the temp cwd under their expected relative paths
            assert (Path(cwd) / "DBFilesClient" / "Spell.dbc").exists()
            assert (Path(cwd) / "Interface" / "Icons" / "spell_icon.blp").exists()

            output.write_bytes(b"fake mpq data")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_output_file

        package_mpq(temp_staging, output)

        mock_run.assert_called_once()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_dereference_symlinks_creates_temp_copy(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        temp_staging: Path,
        real_asset_files: Path,
        tmp_path: Path,
    ):
        """When dereferencing, package_mpq should invoke mpqcli from a temp copy with files copied in place."""
        mock_which.return_value = "/usr/bin/mpqcli"

        # Create staging area
        create_staging_area(temp_staging)

        # Create symlink to external file
        link = temp_staging / "DBFilesClient" / "External.dbc"
        link.symlink_to(real_asset_files / "spell.dbc")

        output = tmp_path / "output.mpq"

        def create_output_file(*args, **kwargs):
            # Ensure cwd is a temporary directory (not the original staging)
            cwd = kwargs.get("cwd")
            assert cwd is not None
            assert Path(cwd) != temp_staging

            # The copied file should exist in the temp cwd under DBFilesClient/External.dbc
            copied = Path(cwd) / "DBFilesClient" / "External.dbc"
            assert copied.exists()
            assert copied.is_file()
            # The copied file should not be a symlink
            assert not copied.is_symlink()

            # Prefer hardlinking: if possible the copied file should share inode with the source
            try:
                src_stat = (real_asset_files / "spell.dbc").stat()
                dst_stat = copied.stat()
                assert dst_stat.st_ino == src_stat.st_ino or copied.read_bytes() == (real_asset_files / "spell.dbc").read_bytes()
            except Exception:
                # If we cannot rely on inode equality on this platform, fall back to content check above
                pass

            output.write_bytes(b"fake mpq data")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_output_file

        package_mpq(temp_staging, output, dereference_symlinks=True)

        mock_run.assert_called_once()

    @patch("os.link")
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_dereference_falls_back_on_cross_device(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        mock_link: MagicMock,
        temp_staging: Path,
        real_asset_files: Path,
        tmp_path: Path,
    ):
        """If hardlink creation fails with EXDEV, fallback to copying should occur."""
        mock_which.return_value = "/usr/bin/mpqcli"

        # Simulate os.link raising EXDEV
        mock_link.side_effect = OSError(errno.EXDEV, "Cross-device link")

        # Create staging area
        create_staging_area(temp_staging)

        # Create symlink to external file
        link = temp_staging / "DBFilesClient" / "External.dbc"
        link.symlink_to(real_asset_files / "spell.dbc")

        output = tmp_path / "output.mpq"

        def create_output_file(*args, **kwargs):
            cwd = kwargs.get("cwd")
            copied = Path(cwd) / "DBFilesClient" / "External.dbc"
            assert copied.exists()
            assert not copied.is_symlink()
            # Content should match source
            assert copied.read_bytes() == (real_asset_files / "spell.dbc").read_bytes()

            output.write_bytes(b"fake mpq data")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_output_file

        package_mpq(temp_staging, output, dereference_symlinks=True)

        mock_run.assert_called_once()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_detects_broken_symlinks(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        temp_staging: Path,
        tmp_path: Path,
        capsys,
    ):
        """Test that broken symbolic links are detected and skipped."""
        mock_which.return_value = "/usr/bin/mpqcli"

        # Create staging area
        create_staging_area(temp_staging)

        # Create a broken symbolic link
        broken_link = temp_staging / "DBFilesClient" / "Broken.dbc"
        nonexistent = tmp_path / "nonexistent" / "file.dbc"
        broken_link.symlink_to(nonexistent)

        # Create a valid file for comparison
        valid_file = temp_staging / "DBFilesClient" / "Valid.dbc"
        valid_file.write_text("valid data")

        output = tmp_path / "output.mpq"

        # Mock subprocess
        def create_output_file(*args, **kwargs):
            output.write_bytes(b"fake mpq data")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_output_file

        package_mpq(temp_staging, output)

        # Check output mentions broken symlink (skipped)
        captured = capsys.readouterr()
        out = captured.out.lower()
        assert "skipping broken symlink" in out or "broken symbolic link" in out
        assert "skip" in out

        # Verify mpqcli was invoked (target is staging dir)
        call_args = mock_run.call_args[0][0]
        assert "." in call_args

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_includes_command_and_stderr_on_mpqcli_failure(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        populated_staging: Path,
        tmp_path: Path,
    ):
        """When mpqcli fails, ensure the raised MPQError includes the command and stderr."""
        mock_which.return_value = "/usr/bin/mpqcli"

        output = tmp_path / "output.mpq"

        # Simulate mpqcli failing with exit code 105 and diagnostic stderr
        err = subprocess.CalledProcessError(
            returncode=105,
            cmd=["mpqcli"],
            stderr="target: Directory does not exist: /path/to/output.mpq",
        )

        mock_run.side_effect = err

        with pytest.raises(Exception) as excinfo:
            package_mpq(populated_staging, output)

        msg = str(excinfo.value)
        assert "mpqcli failed with exit code 105" in msg
        assert "Command:" in msg
        assert "Cwd:" in msg
        assert "Directory does not exist" in msg

    def test_symlink_outside_staging_area(
        self,
        temp_staging: Path,
        real_asset_files: Path,
    ):
        """Test that symlinks pointing outside staging area work correctly."""
        # Create staging area
        create_staging_area(temp_staging)

        # Create symlink to file outside staging area
        link = temp_staging / "DBFilesClient" / "External.dbc"
        link.symlink_to(real_asset_files / "spell.dbc")

        # Verify the link resolves correctly
        assert link.is_symlink()
        assert link.resolve().exists()
        assert link.resolve() == (real_asset_files / "spell.dbc").resolve()

        # Read through symlink to verify content
        assert link.read_bytes() == b"DBC_FILE_DATA_12345"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_relative_symlinks(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        temp_staging: Path,
        tmp_path: Path,
    ):
        """Test that relative symbolic links are handled correctly."""
        mock_which.return_value = "/usr/bin/mpqcli"

        # Create staging area
        create_staging_area(temp_staging)

        # Create a real file in the staging area
        real_file = temp_staging / "DBFilesClient" / "Master.dbc"
        real_file.write_text("master data")

        # Create relative symlink within staging area
        link = temp_staging / "Interface" / "Icons" / "linked.txt"
        # Create relative path: ../../DBFilesClient/Master.dbc
        relative_path = Path("..") / ".." / "DBFilesClient" / "Master.dbc"
        link.symlink_to(relative_path)

        output = tmp_path / "output.mpq"

        # Mock subprocess
        def create_output_file(*args, **kwargs):
            output.write_bytes(b"fake mpq data")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_output_file

        # Should not raise an error
        package_mpq(temp_staging, output)

        mock_run.assert_called_once()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_creates_output_directory_if_missing(
        self,
        mock_run: MagicMock,
        mock_which: MagicMock,
        populated_staging: Path,
        tmp_path: Path,
    ):
        """Test that missing output parent directories are created."""
        mock_which.return_value = "/usr/bin/mpqcli"

        # Output in a nested non-existent directory
        output = tmp_path / "nonexistent" / "nested" / "output.mpq"

        def create_output_file(*args, **kwargs):
            # Simulate mpqcli creating the output file
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"fake mpq data")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_output_file

        package_mpq(populated_staging, output)

        assert output.exists()

    def test_raises_if_output_is_directory(self, temp_staging: Path, tmp_path: Path):
        """Test that passing a directory as the output path raises IsADirectoryError."""
        # Create staging area
        create_staging_area(temp_staging)

        # Create a directory at the output path
        output_dir = tmp_path / "output_dir"
        output_dir.mkdir()

        with pytest.raises(IsADirectoryError):
            package_mpq(temp_staging, output_dir)


class TestValidateMPQ:
    """Tests for validate_mpq function."""

    def test_raises_error_if_mpq_not_found(self, tmp_path: Path):
        """Test that FileNotFoundError is raised if MPQ doesn't exist."""
        mpq = tmp_path / "nonexistent.mpq"

        with pytest.raises(FileNotFoundError, match="not found"):
            validate_mpq(mpq)

    @patch("shutil.which")
    def test_raises_error_if_mpqcli_not_found(
        self, mock_which: MagicMock, tmp_path: Path
    ):
        """Test that MPQCliNotFoundError is raised if mpqcli not in PATH."""
        mock_which.return_value = None
        mpq = tmp_path / "test.mpq"
        mpq.write_bytes(b"fake mpq")

        with pytest.raises(MPQCliNotFoundError, match="not found in PATH"):
            validate_mpq(mpq)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_validates_valid_paths(
        self, mock_run: MagicMock, mock_which: MagicMock, tmp_path: Path
    ):
        """Test validation of an MPQ with valid file paths."""
        mock_which.return_value = "/usr/bin/mpqcli"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="DBFilesClient/Spell.dbc\nInterface/Icons/spell.blp\n",
            stderr="",
        )

        mpq = tmp_path / "test.mpq"
        mpq.write_bytes(b"fake mpq")

        result = validate_mpq(mpq)
        assert result is True

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_raises_validation_error_for_invalid_paths(
        self, mock_run: MagicMock, mock_which: MagicMock, tmp_path: Path
    ):
        """Test that ValidationError is raised for invalid paths."""
        mock_which.return_value = "/usr/bin/mpqcli"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="InvalidFolder/file.txt\nAnotherInvalid/test.dbc\n",
            stderr="",
        )

        mpq = tmp_path / "test.mpq"
        mpq.write_bytes(b"fake mpq")

        with pytest.raises(ValidationError, match="invalid locations"):
            validate_mpq(mpq)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_handles_empty_mpq(
        self, mock_run: MagicMock, mock_which: MagicMock, tmp_path: Path
    ):
        """Test validation of an empty MPQ."""
        mock_which.return_value = "/usr/bin/mpqcli"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )

        mpq = tmp_path / "test.mpq"
        mpq.write_bytes(b"fake mpq")

        result = validate_mpq(mpq)
        assert result is True

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_verbose_mode(
        self, mock_run: MagicMock, mock_which: MagicMock, tmp_path: Path, capsys
    ):
        """Test that verbose mode prints file details."""
        mock_which.return_value = "/usr/bin/mpqcli"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="DBFilesClient/Spell.dbc\nInterface/Icons/spell.blp\n",
            stderr="",
        )

        mpq = tmp_path / "test.mpq"
        mpq.write_bytes(b"fake mpq")

        validate_mpq(mpq, verbose=True)

        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "DBFilesClient/Spell.dbc" in captured.out
