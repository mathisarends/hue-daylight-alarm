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
	body := client.OptNilStartRequest{}
	if command.DurationSeconds > 0 {
		body = client.NewOptNilStartRequest(client.StartRequest{DurationSeconds: command.DurationSeconds})
	}
	result, err := send[*client.AlarmStatusResponse](
		runtime, "start", (*client.Client).StartDaylightAlarm, body)
	if err != nil {
		return err
	}
	return runtime.output(result, func() error {
		return writeRecord(runtime.stdout,
			recordField{Name: "status", Value: result.Status.Or("started")},
			recordField{Name: "duration_seconds", Value: fmt.Sprintf("%d", result.DurationSeconds)},
		)
	})
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
