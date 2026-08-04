package commands

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestProfilesCreateBuildsTypedRequest(t *testing.T) {
	t.Parallel()
	const (
		introID    = "398defb2-fea7-45cd-a668-7e756e706fc4"
		ringtoneID = "bd6af8a6-a692-4c0c-a271-e50b7c9a47f8"
		profileID  = "9d01d00b-343d-4821-9660-2c455d968ce1"
		roomID     = "7a6d3f2e-1111-4a11-9a11-1a2b3c4d5e6f"
		sceneID    = "7a6d3f2e-2222-4a11-9a11-1a2b3c4d5e6f"
	)
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		switch {
		case request.Method == http.MethodGet && request.URL.Path == "/rooms":
			writer.Header().Set("Content-Type", "application/json")
			_, _ = writer.Write([]byte(`[{"id":"` + roomID + `","name":"Bedroom","scenes":[{"id":"` + sceneID + `","name":"Morning"}]}]`))
			return
		case request.Method == http.MethodPost && request.URL.Path == "/alarm-profiles":
		default:
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
			return
		}
		var body map[string]any
		if err := json.NewDecoder(request.Body).Decode(&body); err != nil {
			t.Errorf("decode body: %v", err)
			return
		}
		sunrise := body["sunrise"].(map[string]any)
		if body["name"] != "Weekday" || sunrise["duration_minutes"] != float64(10) || sunrise["scene_id"] != sceneID {
			t.Errorf("body = %#v", body)
		}
		writer.Header().Set("Content-Type", "application/json")
		writer.WriteHeader(http.StatusCreated)
		_, _ = writer.Write([]byte(`{
            "name":"Weekday",
            "intro":{"sound_id":"` + introID + `"},
            "ringtone":{"sound_id":"` + ringtoneID + `","volume":75},
            "sunrise":{"scene_id":"` + sceneID + `","scene_name":"Morning","duration_minutes":10,"brightness_start":1,"brightness_end":100},
            "id":"` + profileID + `",
            "is_default":false
        }`))
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL,
		"profiles", "create", "Weekday",
		"--room=Bedroom",
		"--intro-sound-id="+introID,
		"--ringtone-sound-id="+ringtoneID,
		"--ringtone-volume=75",
		"--scene-name=Morning",
		"--duration-minutes=10",
		"--json", "--compact",
	)
	if exitCode != 0 || !strings.Contains(stdout, `"id":"`+profileID+`"`) {
		t.Fatalf("exit = %d, stdout = %s, stderr = %s", exitCode, stdout, stderr)
	}
}

func TestProfilesCreateValidatesBrightness(t *testing.T) {
	t.Parallel()
	const id = "398defb2-fea7-45cd-a668-7e756e706fc4"
	stdout, stderr, exitCode := runTestCLI(t, "http://unused.invalid",
		"profiles", "create", "Invalid",
		"--room=Bedroom",
		"--intro-sound-id="+id,
		"--ringtone-sound-id="+id,
		"--brightness-start=80",
		"--brightness-end=20",
		"--json",
	)
	if exitCode != 2 || stdout != "" || !strings.Contains(stderr, "starting brightness must be less") {
		t.Fatalf("exit = %d, stdout = %q, stderr = %q", exitCode, stdout, stderr)
	}
}

func TestProfilesDeleteWithYes(t *testing.T) {
	t.Parallel()
	const profileID = "8b2748e3-1234-4567-890a-123456789abc"
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.Method != http.MethodDelete || request.URL.Path != "/alarm-profiles/"+profileID {
			t.Errorf("request = %s %s", request.Method, request.URL.Path)
		}
		writer.WriteHeader(http.StatusNoContent)
	}))
	defer server.Close()

	stdout, stderr, exitCode := runTestCLI(t, server.URL,
		"profiles", "delete", profileID, "--yes", "--json", "--compact",
	)
	if exitCode != 0 || !strings.Contains(stdout, `"deleted":true`) {
		t.Fatalf("exit = %d, stdout = %q, stderr = %q", exitCode, stdout, stderr)
	}
}
