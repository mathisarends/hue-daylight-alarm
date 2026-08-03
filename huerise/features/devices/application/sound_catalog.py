from huerise.features.devices.domain import Sound, SoundCategory, SoundNotFoundError
from huerise.infrastructure.storage import StorageBackend


class SoundCatalog:
    """The sounds available in object storage, keyed by their public id.

    Listing object storage is slow enough to cache, so the catalog is filled
    once and only refreshed when an id misses — new uploads become playable
    without a restart, repeated playback stays cheap.
    """

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage
        self._sounds: dict[str, Sound] | None = None

    async def list_sounds(self, category: SoundCategory | None = None) -> list[Sound]:
        sounds = (await self._load()).values()
        if category is not None:
            sounds = [sound for sound in sounds if sound.category is category]
        return sorted(sounds, key=lambda sound: (sound.category, sound.name))

    async def get(self, sound_id: str) -> Sound:
        sounds = await self._load()
        if sound_id not in sounds:
            sounds = await self._refresh()
        if sound_id not in sounds:
            raise SoundNotFoundError(sound_id)
        return sounds[sound_id]

    async def _load(self) -> dict[str, Sound]:
        if self._sounds is None:
            return await self._refresh()
        return self._sounds

    async def _refresh(self) -> dict[str, Sound]:
        sounds: dict[str, Sound] = {}
        for category in SoundCategory:
            for file in await self._storage.list_files(f"{category.folder}/"):
                sound = Sound.from_storage_path(file.storage_path)
                if sound is not None:
                    sounds[sound.id] = sound
        self._sounds = sounds
        return sounds
