package commands

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestRoomsListJSON(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.URL.Path != "/rooms" {
			t.Errorf("path = %q", request.URL.Path)
		}
		if request.Header.Get("Authorization") != "Bearer test-token" {
			t.Errorf("Authorization = %q", request.Header.Get("Authorization"))
		}
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte(`[{"name":"Bedroom","scene_names":["Sunrise","Relax"]}]`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "rooms", "list", "--fields=name", "--compact")
	if exitCode != 0 {
		t.Fatalf("exit = %d, stderr = %s", exitCode, stderr)
	}
	var rooms []map[string]any
	if err := json.Unmarshal([]byte(stdout), &rooms); err != nil {
		t.Fatal(err)
	}
	if len(rooms) != 1 || len(rooms[0]) != 1 || rooms[0]["name"] != "Bedroom" {
		t.Fatalf("rooms = %#v", rooms)
	}
}

func TestSoundsPreviewSendsGeneratedRequest(t *testing.T) {
	t.Parallel()
	const soundID = "a3d84e9b-bc1d-4550-983d-6abce60cb17b"
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.URL.Path != "/sounds/preview" || request.Method != http.MethodPost {
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			t.Errorf("decode body: %v", err)
			return
		}
		if body["sound_id"] != soundID || body["volume"] != float64(42) {
			t.Errorf("body = %#v", body)
		}
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusAccepted)
		_, _ = writer.Write([]byte(fmt.Sprintf(`{"id":%q,"name":"Shimmer","category":"get_up"}`, soundID)))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "sounds", "preview", soundID, "--volume=42", "--json", "--compact")
	if exitCode != 0 || !strings.Contains(stdout, `"name":"Shimmer"`) {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestSoundsVolumeRejectsOutOfRangeValue(t *testing.T) {
	t.Parallel()
	stdout, stderr, exitCode := runTestCLI(t, "http://unused.invalid", "sounds", "volume", "101", "--json")
	if exitCode != 2 || stdout != "" || !strings.Contains(stderr, `"code": "usage"`) {
		t.Fatalf("exit = %d, stdout = %q, stderr = %q", exitCode, stdout, stderr)
	}
}

func runTestCLI(t *testing.T, baseURL string, args ...string) (string, string, int) {
	t.Helper()
	allArgs := append([]string{"--api-url=" + baseURL, "--token=test-token"}, args...)
	var stdout, stderr bytes.Buffer
	exitCode := Run(context.Background(), allArgs, strings.NewReader(""), &stdout, &stderr)
	return stdout.String(), stderr.String(), exitCode
}
