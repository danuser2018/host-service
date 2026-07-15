from fastapi.testclient import TestClient
from unittest import mock
import pytest
from src.app import create_app
from src.services.audio import HostAudioServiceError

client = TestClient(create_app())

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@mock.patch("src.services.audio.AudioService.get_audio_state")
def test_get_volume_endpoint(mock_get_state):
    mock_get_state.return_value = {"volume": 50, "muted": False}
    response = client.get("/v1/audio/volume")
    assert response.status_code == 200
    assert response.json() == {"volume": 50, "muted": False}

@mock.patch("src.services.audio.AudioService.set_volume")
def test_set_volume_endpoint(mock_set_volume):
    mock_set_volume.return_value = {"volume": 80, "muted": False}
    response = client.post("/v1/audio/volume/set", json={"volume": 80})
    assert response.status_code == 200
    assert response.json() == {"volume": 80, "muted": False}
    mock_set_volume.assert_called_once_with(80)

def test_set_volume_invalid():
    response = client.post("/v1/audio/volume/set", json={"volume": 120})
    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"
    assert response.json()["message"] == "Volume value must be between 0 and 100."

@mock.patch("src.services.audio.AudioService.volume_up")
def test_volume_up_endpoint(mock_up):
    mock_up.return_value = {"volume": 45, "muted": False}
    response = client.post("/v1/audio/volume/up", json={"step": 5})
    assert response.status_code == 200
    assert response.json() == {"volume": 45, "muted": False}
    mock_up.assert_called_once_with(5)

@mock.patch("src.services.audio.AudioService.volume_down")
def test_volume_down_endpoint(mock_down):
    mock_down.return_value = {"volume": 35, "muted": False}
    response = client.post("/v1/audio/volume/down", json={"step": 5})
    assert response.status_code == 200
    assert response.json() == {"volume": 35, "muted": False}
    mock_down.assert_called_once_with(5)

@mock.patch("src.services.audio.AudioService.mute")
def test_mute_endpoint(mock_mute):
    mock_mute.return_value = {"volume": 45, "muted": True}
    response = client.post("/v1/audio/mute")
    assert response.status_code == 200
    assert response.json() == {"volume": 45, "muted": True}

@mock.patch("src.services.audio.AudioService.unmute")
def test_unmute_endpoint(mock_unmute):
    mock_unmute.return_value = {"volume": 45, "muted": False}
    response = client.post("/v1/audio/unmute")
    assert response.status_code == 200
    assert response.json() == {"volume": 45, "muted": False}

@mock.patch("src.services.audio.AudioService.toggle_mute")
def test_toggle_mute_endpoint(mock_toggle):
    mock_toggle.return_value = {"volume": 45, "muted": True}
    response = client.post("/v1/audio/toggle-mute")
    assert response.status_code == 200
    assert response.json() == {"volume": 45, "muted": True}

@mock.patch("src.services.audio.AudioService.get_audio_state")
def test_api_service_unavailable(mock_get_state):
    mock_get_state.side_effect = HostAudioServiceError("The system audio control interface (pactl) is unavailable or failed to execute.")
    response = client.get("/v1/audio/volume")
    assert response.status_code == 503
    assert response.json() == {
        "error": "HOST_AUDIO_SERVICE_UNAVAILABLE",
        "message": "The system audio control interface (pactl) is unavailable or failed to execute.",
        "status": 503
    }
