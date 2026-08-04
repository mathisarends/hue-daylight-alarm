package huerise

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
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

func TestClientRequiresToken(t *testing.T) {
	t.Parallel()
	if _, err := NewClient(Config{BaseURL: DefaultBaseURL}); err == nil {
		t.Fatal("NewClient() unexpectedly accepted an empty token")
	}
}
