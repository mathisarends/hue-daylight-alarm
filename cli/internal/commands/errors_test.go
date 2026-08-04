package commands

import (
	"bytes"
	"errors"
	"io"
	"net/http"
	"strings"
	"testing"

	"github.com/ogen-go/ogen/validate"
)

func TestUnexpectedUnauthorizedResponseIsStructured(t *testing.T) {
	t.Parallel()
	response := &http.Response{
		StatusCode: http.StatusUnauthorized,
		Body:       io.NopCloser(strings.NewReader(`{"detail":"Invalid access token"}`)),
	}
	err := errors.Join(validate.UnexpectedStatusCodeWithResponse(response))
	var output bytes.Buffer
	exitCode := writeError(&output, true, err)
	if exitCode != 3 || !strings.Contains(output.String(), `"code": "auth"`) || !strings.Contains(output.String(), `"status": 401`) {
		t.Fatalf("exit = %d, output = %s", exitCode, output.String())
	}
}
