package commands

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestDrawSunriseShowsProgress(t *testing.T) {
	t.Parallel()
	var out bytes.Buffer
	if err := drawSunrise(&out, 15*time.Minute, 30*time.Minute, 0); err != nil {
		t.Fatal(err)
	}
	line := out.String()
	if !strings.HasPrefix(line, "\r") {
		t.Fatalf("line does not redraw in place: %q", line)
	}
	if !strings.Contains(line, " 50%") || !strings.Contains(line, "15m left") {
		t.Fatalf("line = %q", line)
	}
	if filled := strings.Count(line, "█"); filled != barWidth/2 {
		t.Fatalf("filled = %d, want %d", filled, barWidth/2)
	}
}

func TestFormatRemaining(t *testing.T) {
	t.Parallel()
	for seconds, want := range map[int]string{1: "1s", 15: "15s", 60: "1m", 61: "2m", 3600: "1h"} {
		if got := formatRemaining(time.Duration(seconds) * time.Second); got != want {
			t.Errorf("formatRemaining(%ds) = %q, want %q", seconds, got, want)
		}
	}
}

func TestWatchRefusesJSON(t *testing.T) {
	t.Parallel()
	stdout, stderr, exitCode := runTestCLI(t, "http://127.0.0.1:1", "start", "--watch", "--json")
	if exitCode != 2 || !strings.Contains(stderr, "--watch cannot be combined") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestWatchLeavesTheAlarmRunningWhenInterrupted(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, _ *http.Request) {
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusAccepted)
		_, _ = writer.Write([]byte(`{"status":"started","duration_seconds":600}`))
	}))
	defer server.Close()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	time.AfterFunc(150*time.Millisecond, cancel)

	var stdout, stderr bytes.Buffer
	exitCode := Run(ctx, []string{"--api-url=" + server.URL, "--api-key=test-key", "start", "--watch"},
		strings.NewReader(""), &stdout, &stderr)
	if exitCode != 0 || !strings.Contains(stdout.String(), "keeps fading") {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout.String(), stderr.String())
	}
}
