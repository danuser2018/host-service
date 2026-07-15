from fastapi import APIRouter, Depends
from src.services.audio import AudioService
from src.models.audio import AudioStateResponse, VolumeSetRequest, VolumeStepRequest

router = APIRouter(prefix="/v1/audio")

def get_audio_service() -> AudioService:
    return AudioService()

@router.get("/volume", response_model=AudioStateResponse)
def get_volume(service: AudioService = Depends(get_audio_service)):
    return service.get_audio_state()

@router.post("/volume/set", response_model=AudioStateResponse)
def set_volume(payload: VolumeSetRequest, service: AudioService = Depends(get_audio_service)):
    return service.set_volume(payload.volume)

@router.post("/volume/up", response_model=AudioStateResponse)
def volume_up(payload: VolumeStepRequest, service: AudioService = Depends(get_audio_service)):
    return service.volume_up(payload.step)

@router.post("/volume/down", response_model=AudioStateResponse)
def volume_down(payload: VolumeStepRequest, service: AudioService = Depends(get_audio_service)):
    return service.volume_down(payload.step)

@router.post("/mute", response_model=AudioStateResponse)
def mute(service: AudioService = Depends(get_audio_service)):
    return service.mute()

@router.post("/unmute", response_model=AudioStateResponse)
def unmute(service: AudioService = Depends(get_audio_service)):
    return service.unmute()

@router.post("/toggle-mute", response_model=AudioStateResponse)
def toggle_mute(service: AudioService = Depends(get_audio_service)):
    return service.toggle_mute()
