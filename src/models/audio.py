from pydantic import BaseModel, Field

class AudioStateResponse(BaseModel):
    volume: int = Field(..., ge=0, le=100)
    muted: bool

class VolumeSetRequest(BaseModel):
    volume: int = Field(..., ge=0, le=100)

class VolumeStepRequest(BaseModel):
    step: int = Field(..., ge=0, le=100)
