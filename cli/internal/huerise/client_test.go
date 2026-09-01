package huerise

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestClientSendsAPIKeyHeader(t *testing.T) {
	t.Parallel()
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		if request.URL.Path != "/hue/rooms" {
			t.Errorf("path = %q", request.URL.Path)
		}
		if got := request.Header.Get("X-API-Key"); got != "secret" {
			t.Errorf("X-API-Key = %q", got)
		}
		writer.Header().Set("Content-Type", "application/json")
		_, _ = writer.Write([]byte("[]"))
	}))
	defer server.Close()

	client, err := NewClient(Config{BaseURL: server.URL, APIKey: "secret"})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := client.ListRooms(context.Background()); err != nil {
		t.Fatal(err)
	}
}

func TestClientRequiresAPIKey(t *testing.T) {
	t.Parallel()
	if _, err := NewClient(Config{BaseURL: DefaultBaseURL}); err == nil {
		t.Fatal("NewClient() unexpectedly accepted an empty API key")
	}
}
