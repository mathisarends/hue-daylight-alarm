package huerise

import (
	"testing"
	"time"
)

func TestCredentialsRoundTrip(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)

	if _, err := LoadCredentials(); err == nil {
		t.Fatal("LoadCredentials() unexpectedly found credentials before any were saved")
	}

	want := Credentials{
		AccessToken:  "access-token",
		RefreshToken: "refresh-token",
		ExpiresAt:    time.Now().Add(15 * time.Minute).UTC(),
	}
	if err := SaveCredentials(want); err != nil {
		t.Fatal(err)
	}

	got, err := LoadCredentials()
	if err != nil {
		t.Fatal(err)
	}
	if got.AccessToken != want.AccessToken || got.RefreshToken != want.RefreshToken || !got.ExpiresAt.Equal(want.ExpiresAt) {
		t.Fatalf("LoadCredentials() = %#v, want %#v", got, want)
	}

	if err := ClearCredentials(); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadCredentials(); err == nil {
		t.Fatal("LoadCredentials() unexpectedly found credentials after ClearCredentials()")
	}
	if err := ClearCredentials(); err != nil {
		t.Fatalf("ClearCredentials() on an already-clear store: %v", err)
	}
}
