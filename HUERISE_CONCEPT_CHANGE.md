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
- Parallele Ausführungen sind nicht erlaubt. Ein weiterer Start antwortet mit
  `409 Conflict`.
- `stop` ist idempotent. Ohne laufende Ausführung ist der Aufruf ebenfalls
  erfolgreich.

## HTTP-API

Der fachliche API-Scope besteht nur aus:

| Methode | Route | Verhalten |
| --- | --- | --- |
| `POST` | `/daylight-alarm/start` | Startet die Ausführung, optional mit abweichender Dauer, und antwortet mit `202 Accepted`. |
| `POST` | `/daylight-alarm/stop` | Bricht sie ab und antwortet mit `204 No Content`. |
| `GET` | `/doctor` | Prüft, ob die Konfiguration mit der eingerichteten Hue Bridge ausführbar ist. |
| `GET` | `/rooms` | Listet die Räume und Szenen der eingerichteten Bridge zur Auswahl auf. |
| `GET` | `/scenes` | Listet alle verfügbaren Szenen flach mit ihrem Raum auf. |
| `GET` | `/hue/bridges` | Sucht Bridges und markiert die aktuell ausgewählte Bridge. |
| `GET` | `/hue/bridge` | Liefert den aktuellen Zustand des Onboardings. |
| `PUT` | `/hue/bridge` | Wählt eine gefundene Bridge aus. |
| `POST` | `/hue/bridge/register` | Registriert Huerise nach Betätigung des Link-Buttons an der Bridge. |

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

Ohne Request Body verwendet `start` die vollständige YAML-Konfiguration. Für
eine beschleunigte Vorschau darf ein Client ausschließlich die Dauer dieses
einen Laufs überschreiben:

```json
{"duration_seconds": 10}
```

Szene, Start- und Endhelligkeit kommen immer aus `huerise.yml`. Der Override
wird nicht gespeichert. Eine eigene Demo-Route und Room-/Scene-Parameter sind
damit nicht notwendig.

## Authentifizierung

Es gibt keine Benutzer, Registrierung, Anmeldung, JWTs oder Refresh Tokens mehr.
Geschützte Endpunkte verwenden genau einen statischen API-Key:

- Der Schlüssel kommt aus der Deployment-Umgebung, beispielsweise über
  `HUERISE_API_KEY`, und wird nicht von Huerise gespeichert.
- Clients senden ihn im Header `X-API-Key`.
- `start`, `stop`, `doctor` und alle Hue-Onboarding-Routen sind geschützt.
- Alle API-Routen sind geschützt.

## Hue-Onboarding

Das Hue-Onboarding bleibt als kleine technische Hilfsfunktion erhalten. Sein
Scope ist auf Bridge-Erkennung, Bridge-Auswahl und Registrierung über den
Link-Button begrenzt. Es gibt dabei keine Benutzerzuordnung.

Der API-Flow ist so zustandsorientiert, dass ein beliebiger Client ihn ohne
Kenntnis interner Details darstellen kann:

1. Der Client ruft `GET /hue/bridges` auf und zeigt die gefundenen Bridges an.
2. Mit `PUT /hue/bridge` wählt er eine Bridge anhand ihrer stabilen ID aus.
3. `GET /hue/bridge` meldet danach `link_button_required`.
4. Der Client fordert den Benutzer zum Drücken des Link-Buttons auf und ruft
   `POST /hue/bridge/register` auf. Die API wartet dabei höchstens 60 Sekunden.
5. Nach erfolgreicher Registrierung meldet `GET /hue/bridge` den Zustand
   `ready`. Bei Timeout bleibt die Bridge ausgewählt und der Schritt kann
   wiederholt werden.

Ohne Auswahl meldet der Status `not_selected`. Bei vollständigen
`HUE_BRIDGE_IP`- und `HUE_APP_KEY`-Environment-Overrides meldet er direkt
`ready` und `read_only: true`; Auswahl und Registrierung antworten dann mit
`409 Conflict`.

Bridge-IP und Hue-App-Key dürfen als einzige technische Verbindungsdaten
dauerhaft gespeichert werden. Um keine Datenbank oder zweite Anwendungsablage
zu behalten, werden sie in einem optionalen `hue`-Abschnitt derselben
`huerise.yml` verwaltet:

```yaml
hue:
  bridge_id: "001788fffe000001"
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
- freie Szenen-Aktivierungsroute sowie schreibende Raum- und Szenenverwaltung
- Readiness-Prüfungen, die eine Datenbank voraussetzen
- ein eigener Health-Endpunkt

Die vorhandene Hue-Anbindung und die Logik für den Helligkeitsverlauf können
vereinfacht wiederverwendet werden. Bestehende Abstraktionen werden aber nur
behalten, wenn sie für diesen kleinen Scope noch einen konkreten Zweck erfüllen.

## Technischer Zuschnitt

Die Anwendung bleibt nach Features gegliedert, ohne die bisherigen
Persistenzschichten künstlich nachzubauen:

- `daylight_alarm` besitzt Runner, Start/Stop-Service und API-Routen.
- `lighting` besitzt Hue-Adapter, Doctor, Onboarding und Szenenübersicht.
- gemeinsame Konfiguration, Environment-Settings und API-Key-Authentifizierung
  bleiben kleine Bausteine unterhalb von `huerise` und `huerise.shared`.

Dishka bleibt der Composition Root für App-scoped Services und Adapter. Ports
werden dort injiziert, wo sie Tests oder den Austausch der Hue-Anbindung klarer
machen. Repository-, Unit-of-Work- oder Aggregate-Abstraktionen ohne Persistenz
werden nicht übernommen.

Beide Features sind minimal in `application`, `infrastructure` und
`presentation` gegliedert. Router und Schemas liegen getrennt; die
Presentation-Schicht exportiert ihre öffentlichen Router über `__init__.py`.
Jede API-Operation besitzt eine explizite, stabile `operationId` für generierte
Clients. Tags werden einmalig am jeweiligen Router definiert.

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
7. Räume und Szenen hierarchisch sowie als flache Szenenliste lesbar sind,
8. `start` optional nur die Dauer des aktuellen Laufs überschreiben kann,
9. kein Alarm-, Profil-, Scheduler-, Event- oder Datenbankzustand mehr
   persistiert wird und
10. der Prozess nach einem Neustart allein aus Deployment-Umgebung und YAML-Datei
   wieder betriebsbereit ist.
