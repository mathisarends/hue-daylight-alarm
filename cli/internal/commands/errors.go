package commands

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strings"

	"github.com/mathisarends/huerise/cli/internal/client"
	"github.com/mathisarends/huerise/cli/internal/huerise"
	"github.com/ogen-go/ogen/validate"
)

type commandError struct {
	Code     string
	Message  string
	Hint     string
	Status   int
	ExitCode int
}

func (e *commandError) Error() string { return e.Message }

// apiFailure maps a documented non-success response variant onto a
// commandError. ogen names one type per operation and status, so every variant
// has to be listed even though they share a payload shape.
func apiFailure(operation string, response any) error {
	switch result := response.(type) {
	case *client.ConfigurationErrorResponse:
		return configurationFailure(result)
	case *client.ErrorResponse:
		return apiStatusFailure(result.Detail, http.StatusServiceUnavailable)
	case *client.DoctorNotFound:
		return apiStatusFailure(result.Detail, http.StatusNotFound)
	case *client.DoctorServiceUnavailable:
		return apiStatusFailure(result.Detail, http.StatusServiceUnavailable)
	case *client.RegisterHueBridgeConflict:
		return apiStatusFailure(result.Detail, http.StatusConflict)
	case *client.RegisterHueBridgeServiceUnavailable:
		return apiStatusFailure(result.Detail, http.StatusServiceUnavailable)
	case *client.SelectHueBridgeNotFound:
		return apiStatusFailure(result.Detail, http.StatusNotFound)
	case *client.SelectHueBridgeConflict:
		return apiStatusFailure(result.Detail, http.StatusConflict)
	case *client.SelectHueBridgeServiceUnavailable:
		return apiStatusFailure(result.Detail, http.StatusServiceUnavailable)
	case *client.StartDaylightAlarmNotFound:
		return apiStatusFailure(result.Detail, http.StatusNotFound)
	case *client.StartDaylightAlarmConflict:
		return apiStatusFailure(result.Detail, http.StatusConflict)
	case *client.StartDaylightAlarmServiceUnavailable:
		return apiStatusFailure(result.Detail, http.StatusServiceUnavailable)
	default:
		return fmt.Errorf("unexpected %s response %T", operation, response)
	}
}

func apiStatusFailure(detail string, status int) error {
	return &commandError{Code: "api", Message: detail, Status: status, ExitCode: 1}
}

func configurationFailure(response *client.ConfigurationErrorResponse) error {
	issues := make([]string, 0, len(response.Issues))
	for _, issue := range response.Issues {
		issues = append(issues, issue.Location+": "+issue.Message)
	}
	return &commandError{
		Code:     "configuration",
		Message:  response.Detail,
		Hint:     strings.Join(issues, "; "),
		Status:   http.StatusUnprocessableEntity,
		ExitCode: 2,
	}
}

func normalizeError(err error) error {
	var statusErr *validate.UnexpectedStatusCodeError
	if !errors.As(err, &statusErr) {
		return err
	}
	message := http.StatusText(statusErr.StatusCode)
	if statusErr.Payload != nil && statusErr.Payload.Body != nil {
		body, readErr := io.ReadAll(statusErr.Payload.Body)
		statusErr.Payload.Body = io.NopCloser(bytes.NewReader(body))
		if readErr == nil {
			var payload struct {
				Detail any `json:"detail"`
			}
			if json.Unmarshal(body, &payload) == nil && payload.Detail != nil {
				switch detail := payload.Detail.(type) {
				case string:
					message = detail
				default:
					if encoded, marshalErr := json.Marshal(detail); marshalErr == nil {
						message = string(encoded)
					}
				}
			}
		}
	}
	code, exitCode, hint := "api", 1, ""
	if statusErr.StatusCode == http.StatusUnauthorized || statusErr.StatusCode == http.StatusForbidden {
		code, exitCode = "auth", 3
		hint = "Check HUERISE_API_KEY, or pass --api-key."
	}
	return &commandError{Code: code, Message: message, Hint: hint, Status: statusErr.StatusCode, ExitCode: exitCode}
}

func writeError(writer io.Writer, outputJSON bool, err error) int {
	err = normalizeError(err)
	code, message, hint, status, exitCode := "error", err.Error(), "", 0, 1
	var commandErr *commandError
	var configErr *huerise.ConfigError
	switch {
	case errors.As(err, &commandErr):
		code, message, hint, status = commandErr.Code, commandErr.Message, commandErr.Hint, commandErr.Status
		if commandErr.ExitCode != 0 {
			exitCode = commandErr.ExitCode
		}
	case errors.As(err, &configErr):
		code, message, exitCode = "missing_config", configErr.Message, 2
		hint = configErr.Hint
		if hint == "" {
			hint = "Set HUERISE_API_KEY in the environment or dotenv file."
		}
	}
	if outputJSON {
		details := map[string]any{"code": code, "message": message}
		if hint != "" {
			details["hint"] = hint
		}
		if status != 0 {
			details["status"] = status
		}
		encoder := json.NewEncoder(writer)
		encoder.SetIndent("", "  ")
		_ = encoder.Encode(map[string]any{"error": details})
		return exitCode
	}
	_, _ = fmt.Fprintf(writer, "Error: %s\n", message)
	if hint != "" {
		_, _ = fmt.Fprintf(writer, "Hint: %s\n", hint)
	}
	return exitCode
}
