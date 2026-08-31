package commands

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestFormatDuration(t *testing.T) {
	t.Parallel()
	for seconds, want := range map[int]string{0: "0s", 45: "45s", 1800: "30m", 5400: "1h 30m", 3600: "1h", 90: "1m 30s"} {
		if got := formatDuration(seconds); got != want {
			t.Errorf("formatDuration(%d) = %q, want %q", seconds, got, want)
		}
	}
}

func TestBridgeStatusPointsAtTheNextStep(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, _ *http.Request) {
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte(`{"state":"link_button_required","bridge_id":"bridge-1","ip_address":"192.0.2.10","read_only":false}`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "hue", "bridge", "status")
	if exitCode != 0 || !strings.Contains(stdout, "huerise hue bridge register") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestEmptyBridgeListExplainsWhy(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, _ *http.Request) {
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte(`[]`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "hue", "bridge", "list")
	if exitCode != 0 || !strings.Contains(stdout, "No Hue Bridges found") || !strings.Contains(stdout, "same network") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestStartReportsTheDurationInWords(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, _ *http.Request) {
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusAccepted)
		_, _ = writer.Write([]byte(`{"status":"started","duration_seconds":5400}`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "start")
	if exitCode != 0 || !strings.Contains(stdout, "fading over 1h 30m") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}
