package huerise

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

// Credentials is the token pair a login/register call produced, persisted
// per-machine rather than per-project since it's tied to a person, not a repo.
type Credentials struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
}

// CredentialsPath returns where the CLI stores login state, separate from the
// project-local .env LoadConfig reads.
func CredentialsPath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".huerise", "credentials.json"), nil
}

// LoadCredentials reads the stored token pair, if any.
func LoadCredentials() (Credentials, error) {
	path, err := CredentialsPath()
	if err != nil {
		return Credentials{}, err
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return Credentials{}, err
	}
	var creds Credentials
	if err := json.Unmarshal(data, &creds); err != nil {
		return Credentials{}, err
	}
	return creds, nil
}

// SaveCredentials writes the token pair, creating the containing directory on
// first use. File permissions are user-only: this is a bearer credential.
func SaveCredentials(creds Credentials) error {
	path, err := CredentialsPath()
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(creds, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o600)
}

// ClearCredentials removes the stored token pair. Missing is not an error.
func ClearCredentials() error {
	path, err := CredentialsPath()
	if err != nil {
		return err
	}
	if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
		return err
	}
	return nil
}
