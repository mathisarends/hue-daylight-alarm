package cli

import (
	"bytes"
	"encoding/json"
	"errors"
	"strings"
	"testing"
)

func TestWriteOutputProjectsFields(t *testing.T) {
	t.Parallel()
	var output bytes.Buffer
	err := writeOutput(&output, outputOptions{Fields: "id,name", Compact: true}, []map[string]any{
		{"id": "one", "name": "Wake up", "enabled": true},
	}, func() error { return nil })
	if err != nil {
		t.Fatal(err)
	}
	var rows []map[string]any
	if err := json.Unmarshal(output.Bytes(), &rows); err != nil {
		t.Fatal(err)
	}
	if len(rows) != 1 || len(rows[0]) != 2 || rows[0]["name"] != "Wake up" {
		t.Fatalf("rows = %#v", rows)
	}
}

func TestUnknownFieldIsActionable(t *testing.T) {
	t.Parallel()
	_, err := projectFields(map[string]any{"id": "one", "name": "Wake up"}, "naem")
	if err == nil || !strings.Contains(err.Error(), "unknown field") {
		t.Fatalf("error = %v", err)
	}
	var commandErr *commandError
	if !errors.As(err, &commandErr) || commandErr.Hint != "Available fields: id, name" {
		t.Fatalf("error = %#v", err)
	}
}
