import pytest
import subprocess
from unittest.mock import patch, MagicMock

from src.models.commands import HostCommand, RiskLevel
from src.services.command_executor import CommandExecutor, CommandExecutionError


def test_execute_command_success():
    executor = CommandExecutor()
    cmd = HostCommand(
        name="calculator",
        command=["gnome-calculator"],
        risk=RiskLevel.LOW,
        phrases=["calculadora"],
    )

    mock_process = MagicMock()
    mock_process.pid = 12345

    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        pid = executor.execute(cmd)

        assert pid == 12345
        mock_popen.assert_called_once_with(
            ["gnome-calculator"],
            shell=False,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def test_execute_command_file_not_found():
    executor = CommandExecutor()
    cmd = HostCommand(
        name="backup",
        command=["/usr/local/bin/nonexistent-tool"],
        risk=RiskLevel.MEDIUM,
        phrases=["backup"],
    )

    with patch("subprocess.Popen", side_effect=FileNotFoundError("No such file or directory")):
        with pytest.raises(CommandExecutionError, match="Failed to execute host command 'backup'"):
            executor.execute(cmd)


def test_execute_command_permission_denied():
    executor = CommandExecutor()
    cmd = HostCommand(
        name="restricted",
        command=["/usr/local/bin/restricted-tool"],
        risk=RiskLevel.HIGH,
        phrases=["restricted"],
    )

    with patch("subprocess.Popen", side_effect=PermissionError("Permission denied")):
        with pytest.raises(CommandExecutionError, match="Failed to execute host command 'restricted'"):
            executor.execute(cmd)


def test_execute_command_os_error():
    executor = CommandExecutor()
    cmd = HostCommand(
        name="broken",
        command=["bad-command"],
        risk=RiskLevel.LOW,
        phrases=["broken"],
    )

    with patch("subprocess.Popen", side_effect=OSError("Exec format error")):
        with pytest.raises(CommandExecutionError, match="Failed to execute host command 'broken'"):
            executor.execute(cmd)


def test_execute_command_args_isolation():
    executor = CommandExecutor()
    dangerous_arg = "/tmp; rm -rf /"
    cmd = HostCommand(
        name="list-files",
        command=["ls", "-la", dangerous_arg],
        risk=RiskLevel.LOW,
        phrases=["list files"],
    )

    mock_process = MagicMock()
    mock_process.pid = 9999

    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        pid = executor.execute(cmd)
        assert pid == 9999

        mock_popen.assert_called_once_with(
            ["ls", "-la", dangerous_arg],
            shell=False,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
