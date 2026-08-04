package huerise

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadConfigUsesEnvironmentBeforeDotEnv(t *testing.T) {
	dotEnv := filepath.Join(t.TempDir(), ".env")
	if err := os.WriteFile(dotEnv, []byte("HUERISE_API_URL=http://file.example\nHUERISE_API_TOKEN=file-token\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("HUERISE_API_URL", "http://environment.example/")
	t.Setenv("HUERISE_API_TOKEN", "environment-token")

	config, err := LoadConfig(dotEnv)
	if err != nil {
		t.Fatal(err)
	}
	if config.BaseURL != "http://environment.example" || config.Token != "environment-token" {
		t.Fatalf("LoadConfig() = %#v", config)
	}
}

func TestLoadConfigFallsBackToServerToken(t *testing.T) {
	t.Setenv("HUERISE_API_TOKEN", "")
	t.Setenv("API_ACCESS_TOKEN", "server-token")

	config, err := LoadConfig(filepath.Join(t.TempDir(), "missing.env"))
	if err != nil {
		t.Fatal(err)
	}
	if config.Token != "server-token" {
		t.Fatalf("Token = %q", config.Token)
	}
}
