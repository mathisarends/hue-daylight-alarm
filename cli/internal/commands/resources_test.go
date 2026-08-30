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
		_, _ = writer.Write([]byte(`[{
			"id":"7a6d3f2e-1111-4a11-9a11-1a2b3c4d5e6f",
			"name":"Bedroom",
			"scenes":[
				{"id":"7a6d3f2e-2222-4a11-9a11-1a2b3c4d5e6f","name":"Sunrise"},
				{"id":"7a6d3f2e-3333-4a11-9a11-1a2b3c4d5e6f","name":"Relax"}
			]
		}]`))
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

func TestRoomsDemoSendsGeneratedRequest(t *testing.T) {
	t.Parallel()
	const (
		roomID  = "7a6d3f2e-1111-4a11-9a11-1a2b3c4d5e6f"
		sceneID = "7a6d3f2e-2222-4a11-9a11-1a2b3c4d5e6f"
	)
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		switch {
		case request.Method == http.MethodGet && request.URL.Path == "/rooms":
			writer.Header().Set("Content-Type", "application/json")
			_, _ = writer.Write([]byte(`[{"id":"` + roomID + `","name":"Bedroom","scenes":[{"id":"` + sceneID + `","name":"Sunrise"}]}]`))
			return
		case request.Method == http.MethodPost && request.URL.Path == "/rooms/"+roomID+"/scenes/"+sceneID+"/demo":
		default:
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
			return
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			t.Errorf("decode body: %v", err)
			return
		}
		if body["duration_seconds"] != float64(5) {
			t.Errorf("body = %#v", body)
		}
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusAccepted)
		_, _ = writer.Write([]byte(`{
			"room_id":"` + roomID + `","room_name":"Bedroom",
			"scene_id":"` + sceneID + `","scene_name":"Sunrise",
			"brightness_start":1,"brightness_end":100,
			"steps":25,"step_interval_seconds":0.2,"duration_seconds":5
		}`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL,
		"rooms", "demo", "Bedroom", "Sunrise", "--duration-seconds=5", "--json", "--compact",
	)
	if exitCode != 0 || !strings.Contains(stdout, `"steps":25`) {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func runTestCLI(t *testing.T, baseURL string, args ...string) (string, string, int) {
	t.Helper()
	allArgs := append([]string{"--api-url=" + baseURL, "--token=test-token"}, args...)
	var stdout, stderr bytes.Buffer
	exitCode := Run(context.Background(), allArgs, strings.NewReader(""), &stdout, &stderr)
	return stdout.String(), stderr.String(), exitCode
}
