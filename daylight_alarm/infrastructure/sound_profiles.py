from pathlib import Path
from daylight_alarm.domain.value_objects import AudioFile, SoundProfile, SoundProfileName


class SoundProfileRepository:
    def __init__(self, assets_path: Path = Path("assets")):
        self._assets_path = assets_path
        self._wake_up_path = assets_path / "wake_up_sounds"
        self._get_up_path = assets_path / "get_up_sounds"
        self._profiles: dict[str, SoundProfile] = {}
        self._initialize_profiles()
    
    def _initialize_profiles(self) -> None:
        self._profiles[SoundProfileName.PEACEFUL] = SoundProfile(
            name="Peaceful Morning",
            wake_up_sound=AudioFile(self._wake_up_path / "wake-up-bowls.mp3"),
            get_up_sound=AudioFile(self._get_up_path / "get-up-blossom.mp3"),
            description="Sanfte Klangschalen und blumige Melodien"
        )
        
        self._profiles[SoundProfileName.ENERGETIC] = SoundProfile(
            name="Energetic Start",
            wake_up_sound=AudioFile(self._wake_up_path / "wake-up-gong.mp3"),
            get_up_sound=AudioFile(self._get_up_path / "get-up-shake.mp3"),
            description="Kraftvolle Klänge für einen dynamischen Start"
        )
        
        self._profiles[SoundProfileName.NATURE] = SoundProfile(
            name="Nature Awakening",
            wake_up_sound=AudioFile(self._wake_up_path / "wake-up-jungle.mp3"),
            get_up_sound=AudioFile(self._get_up_path / "get-up-retreat.mp3"),
            description="Natürliche Klänge aus dem Dschungel"
        )
        
        self._profiles[SoundProfileName.COSMIC] = SoundProfile(
            name="Cosmic Journey",
            wake_up_sound=AudioFile(self._wake_up_path / "wake-up-galaxy.mp3"),
            get_up_sound=AudioFile(self._get_up_path / "get-up-aurora.mp3"),
            description="Sphärische Klänge aus dem Universum"
        )
        
        self._profiles[SoundProfileName.MYSTICAL] = SoundProfile(
            name="Mystical Morning",
            wake_up_sound=AudioFile(self._wake_up_path / "wake-up-mist.mp3"),
            get_up_sound=AudioFile(self._get_up_path / "get-up-wisdom.mp3"),
            description="Geheimnisvolle und meditative Klänge"
        )
        
        self._profiles[SoundProfileName.GENTLE] = SoundProfile(
            name="Gentle Awakening",
            wake_up_sound=AudioFile(self._wake_up_path / "wake-up-cherry.mp3"),
            get_up_sound=AudioFile(self._get_up_path / "get-up-shimmer.mp3"),
            description="Besonders sanfte und beruhigende Melodien"
        )
    
    def get(self, profile_name: str) -> SoundProfile:
        if profile_name not in self._profiles:
            raise ValueError(f"Sound profile '{profile_name}' not found")
        return self._profiles[profile_name]
    
    def list_all(self) -> list[SoundProfile]:
        return list(self._profiles.values())
    
    def add_custom(self, profile: SoundProfile) -> None:
        self._profiles[profile.name] = profile
