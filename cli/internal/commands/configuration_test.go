package commands

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

const (
	roomID  = "82fafc26-083d-42e9-bfc5-0f481599b7a3"
	sceneID = "3f4ec112-01c6-4de0-9f7b-f3d6ccc6c898"
	otherID = "109c65f6-c33d-4968-8cda-7d499860a4c8"
)

// configurationServer answers the two calls the wizard makes and records the
// body it was asked to save.
func configurationServer(t *testing.T, saved *map[string]any) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("Content-Type", "application/json")
		switch {
		case request.URL.Path == "/scenes":
			_, _ = writer.Write([]byte(`[
				{"id":"` + sceneID + `","name":"Tageslichtwecker","room_id":"` + roomID + `","room_name":"Mein Zimmer","brightness":0.79},
				{"id":"` + otherID + `","name":"Vapor Wave","room_id":"` + roomID + `","room_name":"Mein Zimmer","brightness":0.79}
			]`))
		case request.Method == http.MethodPut:
			if err := json.NewDecoder(request.Body).Decode(saved); err != nil {
				t.Errorf("decode body: %v", err)
			}
			_, _ = writer.Write([]byte(`{
				"room":{"id":"` + roomID + `","name":"Mein Zimmer"},
				"scene":{"id":"` + sceneID + `","name":"Tageslichtwecker"},
				"duration_seconds":1500,"after_alarm":null
			}`))
		default:
			t.Errorf("unexpected request = %s %s", request.Method, request.URL.Path)
		}
	}))
}

func runWithInput(t *testing.T, baseURL, input string, args ...string) (string, string, int) {
	t.Helper()
	allArgs := append([]string{"--api-url=" + baseURL, "--api-key=test-key"}, args...)
	var stdout, stderr bytes.Buffer
	exitCode := Run(context.Background(), allArgs, strings.NewReader(input), &stdout, &stderr)
	return stdout.String(), stderr.String(), exitCode
}

func TestConfigurationSetAsksWhenIDsAreMissing(t *testing.T) {
	t.Parallel()
	var saved map[string]any
	server := configurationServer(t, &saved)
	defer server.Close()

	stdout, stderr, exitCode := runWithInput(t, server.URL, "1\n25\ny\n", "configuration", "set")
	if exitCode != 0 {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
	if saved["scene_id"] != sceneID || saved["room_id"] != roomID {
		t.Fatalf("saved = %#v", saved)
	}
	if saved["duration_seconds"] != float64(25*60) {
		t.Fatalf("saved = %#v", saved)
	}
	if _, exists := saved["start_brightness"]; exists {
		t.Fatalf("saved = %#v", saved)
	}
	if _, exists := saved["end_brightness"]; exists {
		t.Fatalf("saved = %#v", saved)
	}
	if !strings.Contains(stdout, "Configuration saved.") {
		t.Fatalf("stdout = %s", stdout)
	}
}

func TestConfigurationSetSavesNothingWhenDeclined(t *testing.T) {
	t.Parallel()
	var saved map[string]any
	server := configurationServer(t, &saved)
	defer server.Close()

	stdout, stderr, exitCode := runWithInput(t, server.URL, "1\n25\nn\n", "configuration", "set")
	if exitCode != 0 || !strings.Contains(stdout, "Nothing saved.") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
	if saved != nil {
		t.Fatalf("saved = %#v", saved)
	}
}

func TestConfigurationSetStaysNonInteractiveWithIDs(t *testing.T) {
	t.Parallel()
	var saved map[string]any
	server := configurationServer(t, &saved)
	defer server.Close()

	stdout, stderr, exitCode := runWithInput(t, server.URL, "",
		"configuration", "set", roomID, sceneID, "--duration-seconds=900", "--json", "--compact")
	if exitCode != 0 || !strings.Contains(stdout, `"duration_seconds":1500`) {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
	if saved["duration_seconds"] != float64(900) {
		t.Fatalf("saved = %#v", saved)
	}
}

func TestConfigurationSetRefusesToPromptForJSON(t *testing.T) {
	t.Parallel()
	stdout, stderr, exitCode := runWithInput(t, "http://127.0.0.1:1", "", "configuration", "set", "--json")
	if exitCode != 2 || !strings.Contains(stderr, "required with --json") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestConfigurationSetRejectsHalfTheIdentity(t *testing.T) {
	t.Parallel()
	stdout, stderr, exitCode := runWithInput(t, "http://127.0.0.1:1", "", "configuration", "set", roomID)
	if exitCode != 2 || !strings.Contains(stderr, "belong together") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestConfigurationSetExplainsClosedStdin(t *testing.T) {
	t.Parallel()
	var saved map[string]any
	server := configurationServer(t, &saved)
	defer server.Close()

	stdout, stderr, exitCode := runWithInput(t, server.URL, "", "configuration", "set")
	if exitCode != 2 || !strings.Contains(stderr, "configuration set <room-id> <scene-id>") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}
