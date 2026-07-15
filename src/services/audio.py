import subprocess
import re
import logging

logger = logging.getLogger(__name__)

class HostAudioServiceError(Exception):
    pass

def parse_volume(output: str) -> int:
    match = re.search(r"(\d+)%", output)
    if not match:
        raise ValueError("Could not parse volume from pactl output")
    return int(match.group(1))

def parse_mute(output: str) -> bool:
    return "yes" in output.lower()

def run_pactl(args: list[str]) -> str:
    try:
        import os
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        result = subprocess.run(
            ["pactl"] + args,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
        logger.error(f"pactl command failed: {e}")
        raise HostAudioServiceError("The system audio control interface (pactl) is unavailable or failed to execute.") from e

class AudioService:
    def get_audio_state(self) -> dict:
        volume_out = run_pactl(["get-sink-volume", "@DEFAULT_SINK@"])
        mute_out = run_pactl(["get-sink-mute", "@DEFAULT_SINK@"])
        
        volume = parse_volume(volume_out)
        muted = parse_mute(mute_out)
        return {"volume": volume, "muted": muted}

    def set_volume(self, volume: int) -> dict:
        run_pactl(["set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"])
        return self.get_audio_state()

    def volume_up(self, step: int) -> dict:
        current = self.get_audio_state()
        new_vol = max(0, min(100, current["volume"] + step))
        return self.set_volume(new_vol)

    def volume_down(self, step: int) -> dict:
        current = self.get_audio_state()
        new_vol = max(0, min(100, current["volume"] - step))
        return self.set_volume(new_vol)

    def mute(self) -> dict:
        run_pactl(["set-sink-mute", "@DEFAULT_SINK@", "1"])
        return self.get_audio_state()

    def unmute(self) -> dict:
        run_pactl(["set-sink-mute", "@DEFAULT_SINK@", "0"])
        return self.get_audio_state()

    def toggle_mute(self) -> dict:
        run_pactl(["set-sink-mute", "@DEFAULT_SINK@", "toggle"])
        return self.get_audio_state()
