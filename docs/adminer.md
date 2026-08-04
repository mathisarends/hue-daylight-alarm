# Adminer

Adminer (DB browser) runs at `http://localhost:8080` as part of `docker compose up -d`.

## Login

- **Datenbank System:** SQLite
- **Benutzer:** leer lassen
- **Passwort:** `huerise-dev`
- **Datenbank:** `/data/daylight.db`

## Why a password is needed for a passwordless SQLite file

SQLite has no built-in authentication, but Adminer refuses to log in with an
empty password field by default. Entering a password then fails too, because
the SQLite driver doesn't understand one — you'd see either:

- "Adminer unterstützt den Zugriff auf eine Datenbank ohne Passwort nicht" (empty password), or
- "Die Datenbank unterstützt kein Passwort" (non-empty password)

The fix is the `login-password-less` plugin (`adminer/plugins-enabled/login-password-less.php`),
mounted into the container via `compose.yml`. It checks the password against a
fixed hash but never forwards it to SQLite, so Adminer's login check is
satisfied without the driver ever seeing a password.

## Changing the password

```bash
docker exec daylight-alarm-adminer php -r "echo password_hash('your-new-password', PASSWORD_DEFAULT), PHP_EOL;"
```

Paste the resulting hash into `adminer/plugins-enabled/login-password-less.php`,
then `docker compose up -d adminer` to apply it.
