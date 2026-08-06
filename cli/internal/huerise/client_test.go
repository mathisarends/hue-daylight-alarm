package huerise

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestClientSendsBearerToken(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.URL.Path != "/alarms" {
			t.Errorf("path = %q", request.URL.Path)
		}
		if got := request.Header.Get("Authorization"); got != "Bearer secret" {
			t.Errorf("Authorization = %q", got)
		}
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte("[]"))
	}))
	defer server.Close()

	client, err := NewClient(Config{BaseURL: server.URL, Token: "secret"})
	if err != nil {
		t.Fatal(err)
	}
	alarms, err := client.ListAlarms(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(alarms) != 0 {
		t.Fatalf("alarms = %#v", alarms)
	}
}

func TestClientRequiresTokenOrStoredCredentials(t *testing.T) {
	t.Setenv("HOME", t.TempDir())
	t.Setenv("USERPROFILE", t.TempDir())
	if _, err := NewClient(Config{BaseURL: DefaultBaseURL}); err == nil {
		t.Fatal("NewClient() unexpectedly accepted an empty token with no stored credentials")
	}
}

func TestClientUsesStoredCredentials(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)

	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.URL.Path != "/alarms" {
			t.Errorf("path = %q", request.URL.Path)
		}
		if got := request.Header.Get("Authorization"); got != "Bearer stored-access-token" {
			t.Errorf("Authorization = %q", got)
		}
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte("[]"))
	}))
	defer server.Close()

	if err := SaveCredentials(Credentials{
		AccessToken:  "stored-access-token",
		RefreshToken: "stored-refresh-token",
		ExpiresAt:    time.Now().Add(time.Hour),
	}); err != nil {
		t.Fatal(err)
	}

	client, err := NewClient(Config{BaseURL: server.URL})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := client.ListAlarms(context.Background()); err != nil {
		t.Fatal(err)
	}
}

func TestClientRefreshesAnExpiringAccessToken(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)

	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		switch request.URL.Path {
		case "/auth/refresh":
			writer.Header().Set("Content-Type", "application/json")
			_, _ = writer.Write([]byte(`{"access_token":"rotated-access-token","refresh_token":"rotated-refresh-token","token_type":"bearer","expires_in":900}`))
		case "/alarms":
			if got := request.Header.Get("Authorization"); got != "Bearer rotated-access-token" {
				t.Errorf("Authorization = %q", got)
			}
			writer.Header().Set("Content-Type", "application/json")
			_, _ = writer.Write([]byte("[]"))
		default:
			t.Errorf("path = %q", request.URL.Path)
		}
	}))
	defer server.Close()

	if err := SaveCredentials(Credentials{
		AccessToken:  "stale-access-token",
		RefreshToken: "stored-refresh-token",
		ExpiresAt:    time.Now().Add(time.Second),
	}); err != nil {
		t.Fatal(err)
	}

	client, err := NewClient(Config{BaseURL: server.URL})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := client.ListAlarms(context.Background()); err != nil {
		t.Fatal(err)
	}

	rotated, err := LoadCredentials()
	if err != nil {
		t.Fatal(err)
	}
	if rotated.AccessToken != "rotated-access-token" || rotated.RefreshToken != "rotated-refresh-token" {
		t.Fatalf("LoadCredentials() = %#v", rotated)
	}
}
