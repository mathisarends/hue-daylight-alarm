# Huerise: minimalistischer Zielzustand

## Zweck dieses Dokuments

Dieses Dokument beschreibt den abgestimmten Zielzustand für den grundlegenden
Umbau von Huerise. Es ist noch kein Implementierungsplan. Der Umbau soll die
Anwendung auf genau einen manuell gestarteten Daylight-Alarm reduzieren.

Huerise ist danach kein Alarm- oder Terminverwaltungssystem mehr. Es ist ein
kleiner, zustandsarmer Dienst, der eine Hue-Szene anhand einer YAML-Konfiguration
über einen Zeitraum heller dimmt.

## Kernverhalten

Es gibt genau einen konfigurierten Daylight-Alarm und genau zwei Aktionen:

- `start` liest und validiert die aktuelle YAML-Konfiguration und startet den
  Helligkeitsverlauf sofort.
- `stop` bricht einen laufenden Helligkeitsverlauf ab. Es wird kein weiterer
  Hue-Befehl gesendet; das Licht bleibt deshalb exakt in dem Zustand, den es beim
  Abbruch erreicht hat.

Ein Start aktiviert zuerst die konfigurierte Hue-Szene mit der konfigurierten
Starthelligkeit. Anschließend wird die Helligkeit gleichmäßig bis zur
Endhelligkeit erhöht. Nach Ablauf der Dauer bleibt das Licht bei der
Endhelligkeit. Die Szene wird am Ende nicht erneut aufgerufen.

Es gibt keine Uhrzeit, Wochentage, Zeitzone oder automatische Ausführung. Ein
externer Scheduler wie Home Assistant, cron oder eine Automation kann bei Bedarf
den Start-Endpunkt zu einer bestimmten Zeit aufrufen.

## Konfiguration

Die fachliche Konfiguration liegt in genau einer Datei, standardmäßig
`huerise.yml`:

```yaml
daylight_alarm:
  scene_id: "00000000-0000-0000-0000-000000000000"
  start_brightness: 1
  end_brightness: 100
  duration_seconds: 1800
```

Dabei gilt:

- `scene_id` ist die stabile Hue-Szenen-ID.
- `start_brightness` und `end_brightness` sind Prozentwerte von 1 bis 100.
- `end_brightness` muss größer als `start_brightness` sein.
- `duration_seconds` ist eine positive ganze Zahl.
- Unbekannte Felder sind ungültig, damit Tippfehler nicht unbemerkt bleiben.

Die Datei wird bei jedem `start` und jedem Aufruf von `doctor` neu gelesen.
Änderungen benötigen daher keinen Neustart. Eine bereits laufende Ausführung
verwendet weiterhin den beim Start gelesenen Snapshot.

Die Anwendung schreibt keine Alarmdaten in diese Datei und führt keine Historie.
Die Konfiguration wird ausschließlich vom Betreiber editiert.

## Laufzeitzustand

Der einzige veränderliche fachliche Zustand ist die aktuell laufende
Async-Task. Dieser Zustand lebt nur im Prozessspeicher:

- Ein Prozessneustart beendet eine laufende Ausführung.
- Nach einem Neustart gibt es nichts wiederherzustellen.
- Es werden weder Fortschritt noch vergangene Ausführungen gespeichert.
- Parallele Ausführungen sind nicht erlaubt. Ein zweiter `start` während einer
  laufenden Ausführung antwortet mit `409 Conflict`.
- `stop` ist idempotent. Ohne laufende Ausführung ist der Aufruf ebenfalls
  erfolgreich.

## HTTP-API

Der fachliche API-Scope besteht nur aus:

| Methode | Route | Verhalten |
| --- | --- | --- |
| `POST` | `/daylight-alarm/start` | Startet die Ausführung und antwortet mit `202 Accepted`. |
| `POST` | `/daylight-alarm/stop` | Bricht sie ab und antwortet mit `204 No Content`. |
| `GET` | `/doctor` | Prüft, ob die Konfiguration mit der eingerichteten Hue Bridge ausführbar ist. |
| `GET` | `/health` | Einfache, öffentliche Liveness-Prüfung ohne externe Abhängigkeiten. |

`doctor` ist eine read-only Ende-zu-Ende-Prüfung der Laufbereitschaft. Die Route:

1. liest und validiert `huerise.yml`,
2. prüft, ob vollständige Hue-Zugangsdaten vorhanden sind,
3. verbindet sich mit der Hue Bridge und prüft die Authentifizierung,
4. prüft, ob die konfigurierte Szene existiert und einem steuerbaren Raum
   zugeordnet werden kann.

Die Prüfung verändert kein Licht und startet keinen Helligkeitsverlauf. Nur wenn
alle Checks erfolgreich sind, antwortet sie mit `200 OK`. Andernfalls liefert
sie einen passenden Fehlerstatus und einen konkreten fehlgeschlagenen Check.

Eine eigene Status-, Fortschritts- oder Historienroute gehört nicht zum Scope.

## Authentifizierung

Es gibt keine Benutzer, Registrierung, Anmeldung, JWTs oder Refresh Tokens mehr.
Geschützte Endpunkte verwenden genau einen statischen API-Key:

- Der Schlüssel kommt aus der Deployment-Umgebung, beispielsweise über
  `HUERISE_API_KEY`, und wird nicht von Huerise gespeichert.
- Clients senden ihn im Header `X-API-Key`.
- `start`, `stop`, `doctor` und alle Hue-Onboarding-Routen sind geschützt.
- Nur `/health` bleibt ohne Authentifizierung erreichbar.

## Hue-Onboarding

Das Hue-Onboarding bleibt als kleine technische Hilfsfunktion erhalten. Sein
Scope ist auf Bridge-Erkennung, Bridge-Auswahl und Registrierung über den
Link-Button begrenzt. Es gibt dabei keine Benutzerzuordnung.

Bridge-IP und Hue-App-Key dürfen als einzige technische Verbindungsdaten
dauerhaft gespeichert werden. Um keine Datenbank oder zweite Anwendungsablage
zu behalten, werden sie in einem optionalen `hue`-Abschnitt derselben
`huerise.yml` verwaltet:

```yaml
hue:
  bridge_ip: "192.0.2.10"
  app_key: "secret"

daylight_alarm:
  scene_id: "00000000-0000-0000-0000-000000000000"
  start_brightness: 1
  end_brightness: 100
  duration_seconds: 1800
```

Das Onboarding darf nur diesen `hue`-Abschnitt atomar aktualisieren und muss den
manuell gepflegten Alarmabschnitt unverändert lassen. Alternativ gesetzte
`HUE_BRIDGE_IP`- und `HUE_APP_KEY`-Umgebungsvariablen haben Vorrang und machen
das Schreiben von Hue-Zugangsdaten in die YAML-Datei überflüssig.

## Was entfernt wird

Der neue Scope enthält ausdrücklich nicht mehr:

- Alarm-CRUD, Alarm-IDs, Aktivieren und Deaktivieren von Alarmen
- Alarmprofile und Default-Profile
- Zeitpläne, Wiederholungen, Zeitzonen und den internen Scheduler
- Occurrences, Defects, Fortschrittshistorie und Wiederanlauf
- Datenbank, SQLAlchemy, Alembic und Unit-of-Work-/Repository-Persistenz
- Benutzerverwaltung, Login, JWTs und Refresh Tokens
- Domain-Event-Persistenz, SSE und „next alarm“-Projektionen
- Szenen-Demo, Szenen-Aktivierungsroute sowie Raum- und Szenenverwaltung
- Readiness-Prüfungen, die eine Datenbank voraussetzen

Die vorhandene Hue-Anbindung und die Logik für den Helligkeitsverlauf können
vereinfacht wiederverwendet werden. Bestehende Abstraktionen werden aber nur
behalten, wenn sie für diesen kleinen Scope noch einen konkreten Zweck erfüllen.

## Fehlerverhalten

- Ungültige oder fehlende YAML-Konfiguration: `422 Unprocessable Entity`
- Bereits laufender Alarm bei `start`: `409 Conflict`
- Nicht eingerichtete oder nicht erreichbare Hue Bridge: `503 Service Unavailable`
- Nicht vorhandene konfigurierte Szene: `404 Not Found`
- Falscher oder fehlender API-Key: `401 Unauthorized`

Ein Fehler während der Ausführung beendet die Task und wird geloggt. Er erzeugt
keinen gespeicherten Fehlerzustand und keinen automatischen Retry.

## Abnahmekriterien für den Umbau

Der neue Zielzustand ist erreicht, wenn:

1. eine valide `huerise.yml` den vollständigen Daylight-Alarm beschreibt,
2. `start` die konfigurierte Szene von Start- zu Endhelligkeit fährt,
3. `stop` die Ausführung ohne abschließenden Lichtbefehl beendet,
4. `doctor` die Konfiguration read-only gegen die Hue Bridge prüft und
   verständliche Fehler meldet,
5. alle geschützten Routen ausschließlich den statischen API-Key verwenden,
6. Hue-Onboarding ohne Benutzer- oder Datenbankmodell funktioniert,
7. kein Alarm-, Profil-, Scheduler-, Event- oder Datenbankzustand mehr
   persistiert wird und
8. der Prozess nach einem Neustart allein aus Deployment-Umgebung und YAML-Datei
   wieder betriebsbereit ist.
