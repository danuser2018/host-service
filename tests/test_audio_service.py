import subprocess
from unittest import mock
import pytest
from src.services.audio import AudioService, HostAudioServiceError, parse_volume, parse_mute

def test_parse_volume():
    output = "Volume: front-left: 32841 /  50% / -18,00 dB,   front-right: 32841 /  50% / -18,00 dB"
    assert parse_volume(output) == 50

    output_mono = "Volume: mono: 65536 / 100% / 0.00 dB"
    assert parse_volume(output_mono) == 100

    with pytest.raises(ValueError):
        parse_volume("invalid output")

def test_parse_mute():
    assert parse_mute("Mute: yes") is True
    assert parse_mute("Mute: no") is False
    assert parse_mute("Mute: YES") is True
    assert parse_mute("something else") is False

@mock.patch("subprocess.run")
def test_get_audio_state(mock_run):
    mock_vol = mock.Mock()
    mock_vol.stdout = "Volume: front-left: 32841 /  50% / -18,00 dB"
    mock_mute = mock.Mock()
    mock_mute.stdout = "Mute: no"
    
    mock_run.side_effect = [mock_vol, mock_mute]
    
    service = AudioService()
    state = service.get_audio_state()
    assert state == {"volume": 50, "muted": False}
    assert mock_run.call_count == 2
    mock_run.assert_any_call(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True, check=True, env=mock.ANY)
    mock_run.assert_any_call(["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True, check=True, env=mock.ANY)

@mock.patch("subprocess.run")
def test_set_volume(mock_run):
    mock_vol = mock.Mock()
    mock_vol.stdout = "Volume: front-left: 52428 /  80% / -6,00 dB"
    mock_mute = mock.Mock()
    mock_mute.stdout = "Mute: no"
    
    # Called: 1. set-sink-volume, 2. get-sink-volume, 3. get-sink-mute
    mock_run.side_effect = [mock.Mock(), mock_vol, mock_mute]
    
    service = AudioService()
    state = service.set_volume(80)
    assert state == {"volume": 80, "muted": False}
    assert mock_run.call_count == 3
    mock_run.assert_any_call(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "80%"], capture_output=True, text=True, check=True, env=mock.ANY)

@mock.patch("subprocess.run")
def test_volume_up(mock_run):
    # Current state calls
    mock_vol_1 = mock.Mock()
    mock_vol_1.stdout = "Volume: front-left: 26214 /  40% / -24,00 dB"
    mock_mute_1 = mock.Mock()
    mock_mute_1.stdout = "Mute: no"
    
    # State after set-sink-volume calls
    mock_vol_2 = mock.Mock()
    mock_vol_2.stdout = "Volume: front-left: 29491 /  45% / -21,00 dB"
    mock_mute_2 = mock.Mock()
    mock_mute_2.stdout = "Mute: no"
    
    mock_run.side_effect = [mock_vol_1, mock_mute_1, mock.Mock(), mock_vol_2, mock_mute_2]
    
    service = AudioService()
    state = service.volume_up(5)
    assert state == {"volume": 45, "muted": False}
    mock_run.assert_any_call(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "45%"], capture_output=True, text=True, check=True, env=mock.ANY)

@mock.patch("subprocess.run")
def test_volume_down(mock_run):
    # Current state calls
    mock_vol_1 = mock.Mock()
    mock_vol_1.stdout = "Volume: front-left: 26214 /  40% / -24,00 dB"
    mock_mute_1 = mock.Mock()
    mock_mute_1.stdout = "Mute: no"
    
    # State after set-sink-volume calls
    mock_vol_2 = mock.Mock()
    mock_vol_2.stdout = "Volume: front-left: 22937 /  35% / -27,00 dB"
    mock_mute_2 = mock.Mock()
    mock_mute_2.stdout = "Mute: no"
    
    mock_run.side_effect = [mock_vol_1, mock_mute_1, mock.Mock(), mock_vol_2, mock_mute_2]
    
    service = AudioService()
    state = service.volume_down(5)
    assert state == {"volume": 35, "muted": False}
    mock_run.assert_any_call(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "35%"], capture_output=True, text=True, check=True, env=mock.ANY)

@mock.patch("subprocess.run")
def test_mute(mock_run):
    mock_vol = mock.Mock()
    mock_vol.stdout = "Volume: front-left: 22937 /  35% / -27,00 dB"
    mock_mute = mock.Mock()
    mock_mute.stdout = "Mute: yes"
    
    mock_run.side_effect = [mock.Mock(), mock_vol, mock_mute]
    
    service = AudioService()
    state = service.mute()
    assert state == {"volume": 35, "muted": True}
    mock_run.assert_any_call(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], capture_output=True, text=True, check=True, env=mock.ANY)

@mock.patch("subprocess.run")
def test_unmute(mock_run):
    mock_vol = mock.Mock()
    mock_vol.stdout = "Volume: front-left: 22937 /  35% / -27,00 dB"
    mock_mute = mock.Mock()
    mock_mute.stdout = "Mute: no"
    
    mock_run.side_effect = [mock.Mock(), mock_vol, mock_mute]
    
    service = AudioService()
    state = service.unmute()
    assert state == {"volume": 35, "muted": False}
    mock_run.assert_any_call(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], capture_output=True, text=True, check=True, env=mock.ANY)

@mock.patch("subprocess.run")
def test_pactl_error(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "pactl")
    
    service = AudioService()
    with pytest.raises(HostAudioServiceError):
        service.get_audio_state()

@mock.patch("subprocess.run")
def test_pactl_not_found(mock_run):
    mock_run.side_effect = FileNotFoundError()
    
    service = AudioService()
    with pytest.raises(HostAudioServiceError):
        service.get_audio_state()

@mock.patch("subprocess.run")
def test_pactl_permission_error(mock_run):
    mock_run.side_effect = PermissionError()
    
    service = AudioService()
    with pytest.raises(HostAudioServiceError):
        service.get_audio_state()
