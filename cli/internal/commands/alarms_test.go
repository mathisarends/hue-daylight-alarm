package commands

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
)

func TestAlarmsCreateBuildsSchedule(t *testing.T) {
	t.Parallel()
	const (
		alarmID   = "cb4e584a-6ac0-47ec-a953-0ac4762701f7"
		profileID = "227f8a27-70dd-43ef-9e26-418186aa9282"
		roomID    = "7a6d3f2e-1111-4a11-9a11-1a2b3c4d5e6f"
	)
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		switch {
		case request.Method == http.MethodGet && request.URL.Path == "/rooms":
			writer.Header().Set("Content-Type", "application/json")
			_, _ = writer.Write([]byte(`[{"id":"` + roomID + `","name":"Bedroom","scenes":[]}]`))
			return
		case request.Method == http.MethodPost && request.URL.Path == "/alarms":
		default:
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
			return
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			t.Errorf("decode body: %v", err)
			return
		}
		schedule := body["schedule"].(map[string]any)
		days := schedule["days"].([]any)
		if schedule["hour"] != float64(0) || schedule["minute"] != float64(5) || len(days) != 2 || days[0] != float64(0) || days[1] != float64(4) {
			t.Errorf("body = %#v", body)
		}
		if body["room_id"] != roomID {
			t.Errorf("body = %#v", body)
		}
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusCreated)
		_, _ = writer.Write([]byte(`{
            "id":"` + alarmID + `",
            "label":"Early",
            "schedule":{"hour":0,"minute":5,"timezone":"Europe/Berlin","days":[0,4]},
            "room_id":"` + roomID + `",
            "room_name":"Bedroom",
            "profile_id":"` + profileID + `",
            "is_enabled":true,
            "created_at":"2026-08-04T06:00:00Z",
            "next_occurrence":null
        }`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL,
		"alarms", "create", "Early",
		"--room=Bedroom", "--hour=0", "--minute=5",
		"--day=mon", "--day=fri", "--profile-id="+profileID,
		"--json", "--compact",
	)
	if exitCode != 0 || !strings.Contains(stdout, `"id":"`+alarmID+`"`) {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestAlarmsCreateRejectsUnknownWeekday(t *testing.T) {
	t.Parallel()
	stdout, stderr, exitCode := runTestCLI(t, "http://unused.invalid",
		"alarms", "create", "Invalid", "--room=Bedroom", "--hour=7", "--minute=0", "--day=funday", "--json",
	)
	if exitCode != 2 || stdout != "" || !strings.Contains(stderr, "Choose from: mon, tue") {
		t.Fatalf("exit = %d, stdout = %q, stderr = %q", exitCode, stdout, stderr)
	}
}

func TestAlarmsDeleteNeedsExplicitConfirmationForAutomation(t *testing.T) {
	t.Parallel()
	const alarmID = "cb4e584a-6ac0-47ec-a953-0ac4762701f7"
	var requests atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, _ *http.Request) {
		requests.Add(1)
		writer.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "alarms", "delete", alarmID, "--json", "--no-input")
	if exitCode != 2 || stdout != "" || requests.Load() != 0 || !strings.Contains(stderr, "Pass --yes") {
		t.Fatalf("exit = %d, requests = %d, stdout = %q, stderr = %q", exitCode, requests.Load(), stdout, stderr)
	}
}

func TestAlarmsDeleteWithYes(t *testing.T) {
	t.Parallel()
	const alarmID = "cb4e584a-6ac0-47ec-a953-0ac4762701f7"
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodDelete || request.URL.Path != "/alarms/"+alarmID {
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
		}
		writer.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL, "alarms", "delete", alarmID, "--yes", "--json", "--compact")
	if exitCode != 0 || !strings.Contains(stdout, `"deleted":true`) {
		t.Fatalf("exit = %d, stdout = %q, stderr = %q", exitCode, stdout, stderr)
	}
}
