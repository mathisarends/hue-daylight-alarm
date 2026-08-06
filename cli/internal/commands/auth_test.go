package commands

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/mathisarends/huerise/cli/internal/huerise"
)

func isolateCredentials(t *testing.T) {
	t.Helper()
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("USERPROFILE", home)
}

func TestAuthRegisterStoresCredentials(t *testing.T) {
	isolateCredentials(t)
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodPost || request.URL.Path != "/auth/register" {
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			t.Errorf("decode body: %v", err)
		}
		if body["username"] != "alice" || body["password"] != "correct-horse-battery" {
			t.Errorf("body = %#v", body)
		}
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusCreated)
		_, _ = writer.Write([]byte(`{"access_token":"access-1","refresh_token":"refresh-1","token_type":"bearer","expires_in":900}`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "auth", "register", "--username=alice", "--password=correct-horse-battery")
	if exitCode != 0 || !strings.Contains(stdout, "Registered and logged in as alice") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}

	creds, err := huerise.LoadCredentials()
	if err != nil {
		t.Fatal(err)
	}
	if creds.AccessToken != "access-1" || creds.RefreshToken != "refresh-1" {
		t.Fatalf("LoadCredentials() = %#v", creds)
	}
}

func TestAuthLoginStoresCredentials(t *testing.T) {
	isolateCredentials(t)
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodPost || request.URL.Path != "/auth/login" {
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
		}
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte(`{"access_token":"access-2","refresh_token":"refresh-2","token_type":"bearer","expires_in":900}`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "auth", "login", "--username=bob", "--password=s3cret-passphrase")
	if exitCode != 0 || !strings.Contains(stdout, "Logged in as bob") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestAuthLoginRejectsWrongPassword(t *testing.T) {
	isolateCredentials(t)
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusUnauthorized)
		_, _ = writer.Write([]byte(`{"detail":"Invalid credentials"}`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "auth", "login", "--username=bob", "--password=wrong")
	if exitCode != 3 || stdout != "" || !strings.Contains(stderr, "Invalid credentials") {
		t.Fatalf("exit = %d, stdout = %q, stderr = %q", exitCode, stdout, stderr)
	}
	if _, err := huerise.LoadCredentials(); err == nil {
		t.Fatal("LoadCredentials() unexpectedly found credentials after a rejected login")
	}
}

func TestAuthRegisterRequiresCredentialsWithoutInput(t *testing.T) {
	isolateCredentials(t)
	stdout, stderr, exitCode := runTestCLI(t, "http://unused.invalid", "auth", "register", "--no-input")
	if exitCode != 2 || stdout != "" || !strings.Contains(stderr, "username is required") {
		t.Fatalf("exit = %d, stdout = %q, stderr = %q", exitCode, stdout, stderr)
	}
}

func TestAuthLogoutClearsCredentialsAndRevokesServerSide(t *testing.T) {
	isolateCredentials(t)
	if err := huerise.SaveCredentials(huerise.Credentials{AccessToken: "access-3", RefreshToken: "refresh-3"}); err != nil {
		t.Fatal(err)
	}

	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodPost || request.URL.Path != "/auth/logout" {
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			t.Errorf("decode body: %v", err)
		}
		if body["refresh_token"] != "refresh-3" {
			t.Errorf("body = %#v", body)
		}
		writer.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "auth", "logout")
	if exitCode != 0 || !strings.Contains(stdout, "Logged out.") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
	if _, err := huerise.LoadCredentials(); err == nil {
		t.Fatal("LoadCredentials() unexpectedly found credentials after logout")
	}
}

func TestAuthLogoutClearsCredentialsEvenIfServerUnreachable(t *testing.T) {
	isolateCredentials(t)
	if err := huerise.SaveCredentials(huerise.Credentials{AccessToken: "access-4", RefreshToken: "refresh-4"}); err != nil {
		t.Fatal(err)
	}

	stdout, stderr, exitCode := runTestCLI(t, "http://unused.invalid", "auth", "logout")
	if exitCode != 0 || !strings.Contains(stdout, "Logged out.") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
	if _, err := huerise.LoadCredentials(); err == nil {
		t.Fatal("LoadCredentials() unexpectedly found credentials after logout")
	}
}
