package commands

import (
	"fmt"

	"github.com/mathisarends/huerise/cli/internal/client"
)

type startCommand struct {
	DurationSeconds int `name:"duration-seconds" help:"Override the configured sunrise duration."`
}

type stopCommand struct{}

func (command startCommand) Run(runtime *Runtime) error {
	if command.DurationSeconds < 0 {
		return &commandError{Code: "usage", Message: "duration must be positive", ExitCode: 2}
	}
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	body := client.OptNilStartRequest{}
	if command.DurationSeconds > 0 {
		body = client.NewOptNilStartRequest(client.StartRequest{DurationSeconds: command.DurationSeconds})
	}
	response, err := apiClient.StartDaylightAlarm(runtime.ctx, body)
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.AlarmStatusResponse:
		return runtime.output(result, func() error {
			return writeRecord(runtime.stdout,
				recordField{Name: "status", Value: result.Status.Or("started")},
				recordField{Name: "duration_seconds", Value: fmt.Sprintf("%d", result.DurationSeconds)},
			)
		})
	default:
		return apiFailure("start", response)
	}
}

func (stopCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	if err := apiClient.StopDaylightAlarm(runtime.ctx); err != nil {
		return err
	}
	return runtime.output(map[string]any{"stopped": true}, func() error {
		_, err := fmt.Fprintln(runtime.stdout, "Stopped.")
		return err
	})
}
