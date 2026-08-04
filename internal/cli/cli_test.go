package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"strings"
	"testing"
)

func TestNoArgumentsPrintsHelp(t *testing.T) {
	t.Parallel()
	var stdout, stderr bytes.Buffer
	if exitCode := Run(context.Background(), nil, strings.NewReader(""), &stdout, &stderr); exitCode != 0 {
		t.Fatalf("exit = %d, stderr = %s", exitCode, stderr.String())
	}
	if !strings.Contains(stdout.String(), "Usage: huerise") {
		t.Fatalf("stdout = %s", stdout.String())
	}
}

func TestVersionSupportsJSON(t *testing.T) {
	t.Parallel()
	var stdout, stderr bytes.Buffer
	exitCode := Run(context.Background(), []string{"version", "--json", "--compact"}, strings.NewReader(""), &stdout, &stderr)
	if exitCode != 0 {
		t.Fatalf("exit = %d, stderr = %s", exitCode, stderr.String())
	}
	var result map[string]any
	if err := json.Unmarshal(stdout.Bytes(), &result); err != nil {
		t.Fatal(err)
	}
	if result["version"] != Version {
		t.Fatalf("result = %#v", result)
	}
}

func TestUsageErrorIsJSONWhenRequested(t *testing.T) {
	t.Parallel()
	var stdout, stderr bytes.Buffer
	exitCode := Run(context.Background(), []string{"not-a-command", "--json"}, strings.NewReader(""), &stdout, &stderr)
	if exitCode != 2 || stdout.Len() != 0 || !strings.Contains(stderr.String(), `"code": "usage"`) {
		t.Fatalf("exit = %d, stdout = %q, stderr = %q", exitCode, stdout.String(), stderr.String())
	}
}
