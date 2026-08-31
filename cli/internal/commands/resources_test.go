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

func TestScenesList(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.URL.Path != "/scenes" {
			t.Errorf("path = %q", request.URL.Path)
		}
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte(`[{
			"id":"7a6d3f2e-2222-4a11-9a11-1a2b3c4d5e6f","name":"Sunrise",
			"room_id":"7a6d3f2e-1111-4a11-9a11-1a2b3c4d5e6f","room_name":"Bedroom","brightness":null
		}]`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "scenes")
	if exitCode != 0 || !strings.Contains(stdout, "Sunrise") || !strings.Contains(stdout, "Bedroom") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestStartSendsDurationOverride(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodPost || request.URL.Path != "/daylight-alarm/start" {
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
			return
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			t.Errorf("decode body: %v", err)
			return
		}
		if body["duration_seconds"] != float64(60) {
			t.Errorf("body = %#v", body)
		}
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusAccepted)
		_, _ = writer.Write([]byte(`{"status":"started","duration_seconds":60}`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "start", "--duration-seconds=60", "--json", "--compact")
	if exitCode != 0 || !strings.Contains(stdout, `"duration_seconds":60`) {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestStop(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodPost || request.URL.Path != "/daylight-alarm/stop" {
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
		}
		writer.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "stop")
	if exitCode != 0 || !strings.Contains(stdout, "Stopped.") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func runTestCLI(t *testing.T, baseURL string, args ...string) (string, string, int) {
	t.Helper()
	allArgs := append([]string{"--api-url=" + baseURL, "--api-key=test-key"}, args...)
	var stdout, stderr bytes.Buffer
	exitCode := Run(context.Background(), allArgs, strings.NewReader(""), &stdout, &stderr)
	return stdout.String(), stderr.String(), exitCode
}
