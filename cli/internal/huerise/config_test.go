package huerise

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadConfigUsesEnvironmentBeforeDotEnv(t *testing.T) {
	dotEnv := filepath.Join(t.TempDir(), ".env")
	if err := os.WriteFile(dotEnv, []byte("HUERISE_API_URL=http://file.example\nHUERISE_API_KEY=file-key\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("HUERISE_API_URL", "http://environment.example/")
	t.Setenv("HUERISE_API_KEY", "environment-key")

	config, err := LoadConfig(dotEnv)
	if err != nil {
		t.Fatal(err)
	}
	if config.BaseURL != "http://environment.example" || config.APIKey != "environment-key" {
		t.Fatalf("LoadConfig() = %#v", config)
	}
}

func TestLoadConfigReadsDotEnv(t *testing.T) {
	dotEnv := filepath.Join(t.TempDir(), ".env")
	if err := os.WriteFile(dotEnv, []byte("HUERISE_API_KEY=file-key\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("HUERISE_API_URL", "")
	t.Setenv("HUERISE_API_KEY", "")

	config, err := LoadConfig(dotEnv)
	if err != nil {
		t.Fatal(err)
	}
	if config.BaseURL != DefaultBaseURL || config.APIKey != "file-key" {
		t.Fatalf("LoadConfig() = %#v", config)
	}
}
