# Multi-Tenant-Support

## Ziel

Huerise soll weiterhin als eine einzelne lokale Installation auf einem Raspberry
Pi betrieben werden können, aber mehrere voneinander getrennte Benutzer bzw.
Tenants unterstützen. Jeder Tenant soll nur die eigenen Alarme, Profile,
Einstellungen und Ereignisse sehen und verändern können.

Die Mandantentrennung betrifft nicht nur die HTTP-API und die Datenbank. Sie
muss auch für Hintergrundprozesse wie Scheduler und Runner sowie für den
Event-Stream gelten.

## Fachliches Modell

Ein Tenant repräsentiert eine logisch getrennte Nutzungseinheit innerhalb der
Installation. Benutzer erhalten über ihre Anmeldung bzw. ihr Zugriffstoken
einen eindeutigen Tenant-Kontext. Falls später mehrere Benutzer gemeinsam zu
einem Tenant gehören sollen, kann das Modell um Mitgliedschaften und Rollen
erweitert werden, ohne die eigentliche Mandantentrennung zu verändern.

Hue-Räume und Audio-Ausgänge werden explizit einem Tenant zugeordnet. Ein
Tenant soll mindestens einen Raum verwenden können; das Modell sollte aber
nicht unnötig auf exakt einen Raum beschränkt werden. Dadurch bleiben spätere
Anwendungsfälle mit mehreren Räumen oder Ausgabegeräten möglich.

Physische Ressourcen werden zunächst exklusiv zugeordnet:

- Ein Hue-Raum gehört höchstens einem Tenant.
- Ein konkreter Audio-Ausgang bzw. Lautsprecher gehört höchstens einem Tenant.
- Ein Alarm darf nur Räume, Szenen, Profile und Audio-Ausgänge seines eigenen
  Tenants referenzieren.
- Eine Szene muss zum ausgewählten Hue-Raum gehören.

Durch diese Exklusivität können Alarme verschiedener Tenants parallel laufen,
solange sie unterschiedliche Hardware verwenden. Eine globale Einschränkung
auf nur einen aktiven Alarm ist daher nicht vorgesehen.

## Identität und Zugriff

Die derzeitige Prüfung eines einzelnen globalen API-Tokens muss durch eine
Authentifizierung ersetzt werden, die neben der Gültigkeit des Zugriffs auch
den Benutzer und Tenant bestimmt. Dieser Tenant-Kontext muss für die gesamte
Bearbeitung eines Requests verfügbar sein.

Die eigentliche Sicherheitsgrenze soll in der Datenzugriffsschicht erzwungen
werden. Es darf nicht davon abhängen, dass jeder einzelne Router oder Service
freiwillig einen passenden Filter setzt. Lesen, Ändern und Löschen anhand einer
ID muss immer auch die Tenant-Zugehörigkeit berücksichtigen. Der Zugriff auf
eine existierende Ressource eines anderen Tenants soll sich nach außen wie eine
nicht vorhandene Ressource verhalten.

Systemweite Hintergrundprozesse benötigen einen ausdrücklich erkennbaren
privilegierten Zugriff. Dieser darf nicht versehentlich auch für normale
Requests verwendet werden.

## Daten und Besitz

Tenant-abhängige Daten erhalten eine eindeutige Tenant-Zuordnung. Dazu gehören
mindestens Alarme, Alarmprofile und Alarm-Occurrences. Auch dort, wo sich der
Tenant indirekt über eine Beziehung herleiten ließe, darf eine direkte
Zuordnung verwendet werden, wenn sie Abfragen, Isolation oder die Verarbeitung
im Hintergrund sicherer macht.

Eindeutigkeitsregeln müssen innerhalb eines Tenants gelten, sofern es sich
nicht tatsächlich um eine installationsweit eindeutige Ressource handelt. So
sollen beispielsweise verschiedene Tenants Profile mit demselben Namen
besitzen können.

Der mitgelieferte Sound-Katalog kann zunächst installationsweit gemeinsam
genutzt werden. Benutzerdefinierte Uploads würden später eine eigene
Besitzregel benötigen.

Bestehende Daten müssen bei der Einführung einem initialen Tenant zugeordnet
werden, sodass eine vorhandene Einzelbenutzer-Installation nach dem Upgrade
weiter funktioniert. Die konkrete Migrations- und Übergangsstrategie soll bei
der Implementierung anhand des dann aktuellen Schemas festgelegt werden.

## Hardware-Zuordnung und Validierung

Beim Anlegen oder Ändern eines Alarms muss Huerise validieren, dass alle
referenzierten Ressourcen zusammenpassen:

1. Der ausgewählte Raum ist auf der Hue Bridge vorhanden.
2. Der Raum ist dem aktuellen Tenant zugeordnet.
3. Die ausgewählte Szene gehört zu diesem Raum.
4. Das Profil gehört zum aktuellen Tenant.
5. Der Audio-Ausgang gehört zum aktuellen Tenant und ist verfügbar.

Wie Szene und Audio-Ausgang fachlich zwischen Alarm und Profil aufgeteilt
werden, ist bewusst keine feste Vorgabe dieses Plans. Bei der Implementierung
soll entschieden werden, welches Modell die vorhandenen Aggregate am klarsten
hält. Wichtig ist die durchgängige Validierung der resultierenden
Ressourcenbeziehungen.

Die aktuelle globale Auswahl eines Audio-Backends bzw. Sonos-Lautsprechers
muss tenant- oder ressourcenbezogen werden. Insbesondere darf das Stoppen,
Snoozen oder Beenden eines Alarms nicht die Audioausgabe eines anderen Tenants
beeinflussen.

## Gleichzeitige Ausführung

Exklusive Ressourcenzuordnung verhindert Konflikte zwischen verschiedenen
Tenants, beseitigt aber nicht zwangsläufig Konflikte zwischen zwei Alarmen
desselben Tenants. Zwei Alarme können beispielsweise gleichzeitig denselben
Raum oder Audio-Ausgang verwenden.

Falls dafür Koordination notwendig ist, soll sie pro konkreter Ressource und
nicht global für die gesamte Installation erfolgen. Die Implementierung kann
geeignete Konfliktregeln oder Laufzeitsperren wählen. Unabhängige Räume und
Audio-Ausgänge sollen weiterhin parallel betrieben werden können.

## Scheduler, Runner und Gerätesynchronisation

Scheduler und andere Hintergrundprozesse müssen Alarme tenantübergreifend
finden dürfen, die weitere Verarbeitung aber stets mit dem Tenant der
jeweiligen Ressource durchführen. Beim Nachladen von Alarmen, Profilen oder
Occurrences muss die Zugehörigkeit erhalten und geprüft werden.

Auch Reaktionen auf Änderungen der Hue Bridge müssen die Ressourcenzuordnung
beachten. Eine umbenannte oder entfernte Szene bzw. ein Raum darf nur die
Tenants und Alarme beeinflussen, denen diese Hardware zugeordnet ist.

## Events und Server-Sent Events

Jedes intern veröffentlichte Event muss einem Tenant zugeordnet werden können.
Subscriptions dürfen ausschließlich Events des authentifizierten Tenants
erhalten. Das gilt sowohl für Live-Events als auch für das Replay nach einer
Wiederverbindung.

Abgeleitete Zustände wie der nächste Alarm müssen ebenfalls pro Tenant geführt
werden. Ein globaler Zustand für die gesamte Installation ist dafür nicht
ausreichend.

## Sicherheits- und Verhaltenstests

Die Implementierung soll insbesondere folgende Eigenschaften absichern:

- Ein Tenant kann die Ressourcen eines anderen Tenants weder auflisten noch
  über bekannte IDs lesen, ändern oder löschen.
- Fremde Profile, Räume, Szenen und Audio-Ausgänge können keinem Alarm
  zugewiesen werden.
- Scheduler und Runner verarbeiten Ressourcen mit dem richtigen
  Tenant-Kontext.
- Live-Events und Replay bleiben tenant-isoliert.
- Das Stoppen oder Snoozen eines Alarms wirkt nur auf dessen konkrete
  Audio-Ressource.
- Alarme auf unabhängiger Hardware können parallel laufen.
- Vorhandene Einzelbenutzerdaten funktionieren nach der Migration unter dem
  initialen Tenant weiter.

## Nicht festgelegt

Dieser Plan beschreibt die fachlichen Grenzen, legt aber bewusst keine
konkreten Endpoints, Klassennamen, Dependency-Injection-Technik, Tokenformate
oder Reihenfolge einzelner Commits fest. Ebenso bleibt offen, ob die erste
Version bereits Benutzerrollen, Einladungen oder mehrere Mitgliedschaften pro
Benutzer unterstützt.

Diese Entscheidungen soll der implementierende Agent anhand der dann
vorhandenen Codebasis treffen. Maßgeblich sind die Tenant-Isolation, die
explizite Hardware-Zuordnung und die Vermeidung globaler Seiteneffekte.
