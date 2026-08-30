# Huerise auf Lichtautomation beschränken

## Ziel

Huerise soll künftig ausschließlich Lichtautomation sein (Hue-Bridge, Räume,
Szenen, Sunrise-Ramp, Scheduler/Runner-Intervall-Logik). Die gesamte
Sound-/Sonos-Logik (lokale Sounddateien speichern/abspielen, Sonos-Lautsprecher
auswählen und ansteuern, Audio-Output umschalten) wird aus dem Projekt entfernt.

Der Alarm bleibt als Konzept bestehen ("Wecker, der das Licht hochfährt"),
verliert aber Intro- und Ringtone-Sound. Was übrig bleibt, ist im Kern der
Scheduler/Runner-Tick, der in einem Intervall prüft, ob ein Alarm fällig ist,
und dann die Sunrise-Ramp (Licht langsam hochfahren, nicht abschalten) fährt.

## Vollständig zu entfernende Dateien

**`features/lighting` — Sound/Sonos/Audio:**
- `application/sonos_speaker_service.py`
- `application/sound_service.py`
- `application/audio_output.py` (`AudioOutputService`, `SwitchableAudioPlayer`)
- `domain/audio_output.py` (`AudioOutput` Enum, `AudioOutputUnavailableError`)
- `domain/sonos_speaker.py`
- `domain/sonos_speaker_repository.py`
- `domain/sound.py`
- `domain/sound_repository.py`
- `infrastructure/sonos.py` (`SonosAudioPlayer`, nutzt `sonosify`)
- `infrastructure/sound_device.py` (`SoundDeviceAudioPlayer`, nutzt `sounddevice`/`soundfile`)
- `presentation/audio_output_router.py`
- `presentation/sound_router.py`
- `AudioPlayer`/`SonosSpeakerSelector` Ports in `application/ports.py`

**`features/alarm`:**
- Intro-/Ringtone-Teile aus `domain/alarm.py`, `domain/profile.py`,
  `domain/views.py` (`IntroConfig`, `RingtoneConfig`) entfernen, `SunriseConfig`
  bleibt.
- `presentation/profile_schemas.py`: `IntroSchema`, `RingtoneSchema` entfernen;
  `ProfileCreate`/`ProfileRead` verlieren `intro`/`ringtone`.

**`features/events`:**
- `OccurrenceRinging`-Event (trägt `sound_id`, `volume`) entfernen oder durch ein
  reines "Sunrise fertig"-Event ersetzen.
- `ProfileSnapshot`/`SunriseSnapshot` bleiben, Sound-Bezug in Kommentaren
  entfernen.

**`features/runner/application/runner.py`:**
- `AudioPlayer`-Abhängigkeit, `_run_ringtone`, `_INTRO_VOLUME`, Intro-Task
  (`_intro_finished`, `self._intro_tasks`) komplett entfernen.
- `run()` endet nach `_light_up()` (Sunrise fertig = Occurrence fertig), kein
  `_start_ringing()`/`_run_ringtone()` mehr.
- `OccurrenceState.RINGING` wird dann nicht mehr erreicht — prüfen, ob der State
  komplett entfernt wird oder nur unbenutzt bleibt (siehe offene Fragen).

**Sonstiges:**
- `features/lighting/application/doctor_service.py`: `sonos_speaker`-Check
  entfernen, `DoctorStatus.configured` nur noch von `hue_bridge` abhängig.
- `features/lighting/infrastructure/settings.py`: `AudioSettings`,
  `SonosSettings` entfernen.
- `features/lighting/infrastructure/di.py` (`LightingProvider`): alle
  Sound-/Sonos-/Audio-Provider entfernen (`sound_repository`,
  `sonos_speaker_repository`, `audio_settings`, `sonos_settings`,
  `switchable_audio`, `audio` alias, `sound_service`, `audio_output_service`,
  `sonos_speaker_service`), `doctor_service`-Provider anpassen (kein
  `SonosSpeakerRepository`-Param mehr).
- `features/lighting/presentation/schemas.py`, `exception_mappings.py`,
  `doctor_schemas.py`: Sound-/Sonos-bezogene Schemas/Exception-Mappings
  entfernen.
- `infrastructure/storage/*`: prüfen, ob `StorageBackend` nur für
  Sound-Dateien existierte (dann ganz entfernen) oder noch anderweitig
  gebraucht wird.

**Datenbank (`infrastructure/database/models.py` + Alembic-Migration):**
- `SoundModel` (`sounds`-Tabelle) entfernen.
- `SonosSpeakerSelectionModel` (`sonos_speaker_selection`-Tabelle) entfernen.
- `AlarmProfileModel`: Spalten `intro_sound_id`, `ringtone_sound_id`,
  `ringtone_volume` entfernen.
- Neue Alembic-Revision schreiben, die diese Tabellen/Spalten droppt.

**Dependencies (`pyproject.toml`):**
- Optionale Gruppen `local` (`numpy`, `sounddevice`, `soundfile`) und `sonos`
  (`sonosify`) komplett entfernen.
- Projektbeschreibung `"Philips Hue sunrise alarm system"` bleibt sinngemäß
  passend, ggf. auf reine Licht-/Sunrise-Automation umformulieren.

## Was unverändert bleibt

- `features/lighting/application/hue_bridge_service.py`, `scene_service.py`,
  `sunrise_demo.py` (reine Licht-Logik, kein Sound).
- `features/lighting/infrastructure/hue.py`, `domain/hue_bridge*.py`,
  `domain/room.py`, `domain/light_change.py`, `domain/sunrise.py`.
- `features/scheduler/application/scheduler.py` — der Intervall-Tick
  (`_TICK_INTERVAL`, `_LOOKAHEAD`, `_GRACE_PERIOD`), der Occurrences
  materialisiert und fällige Alarme an den Runner übergibt, bleibt exakt so.
  Das ist der Kern von "Licht schaltet nicht einfach ab, sondern läuft in
  einem Intervall/einer Rampe".
- `features/alarm` als Ganzes bleibt (Schedule, Weekday, Alarm-Regeln,
  Occurrences, Sunrise-Profile) — nur ohne Sound-Teile.
- `features/auth`, `features/user` unverändert.

## Offene Fragen (vor Umsetzung klären)

1. **`OccurrenceState.RINGING`/`SNOOZED`/`OccurrenceRinging`-Event:** Bleibt der
   Zustand "klingelt" als reines Licht-Ereignis bestehen (z. B. Licht auf voller
   Helligkeit halten bis Dismiss), oder ist eine Occurrence nach Ende der
   Sunrise-Ramp direkt `DISMISSED`/fertig? Das entscheidet, wie viel vom
   Occurrence-State-Machine-Code (`snooze`, `ring`, `dismiss` in
   `domain/occurrence.py`) erhalten bleibt.
2. **Frontend/Clients:** Gibt es Consumer (App, Display), die `sound_id`,
   `/sounds`, `/audio-output`, `/sonos` Endpunkte nutzen? Die müssen parallel
   angepasst werden.
3. **Bestehende Daten:** Sollen vorhandene Sound-Dateien im Storage-Backend
   beim Migrationslauf mit gelöscht werden, oder reicht das Entfernen der
   DB-Referenzen?
4. **Name/Beschreibung des Projekts:** Soll `pyproject.toml`
   `description` und ggf. der Projektname noch den Wecker-/Alarm-Charakter
   behalten oder rein auf "Lichtautomation" umbenannt werden?
