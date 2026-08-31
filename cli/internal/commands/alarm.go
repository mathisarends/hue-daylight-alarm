package commands

import (
	"fmt"
	"time"

	"github.com/mathisarends/huerise/cli/internal/client"
)

type startCommand struct {
	DurationSeconds int  `name:"duration-seconds" help:"Override the configured sunrise duration."`
	Watch           bool `help:"Follow the fade in the terminal; leaving does not stop the alarm."`
}

type stopCommand struct{}

func (command startCommand) Run(runtime *Runtime) error {
	if command.DurationSeconds < 0 {
		return &commandError{Code: "usage", Message: "duration must be positive", ExitCode: 2}
	}
	if command.Watch && (runtime.root.JSON || runtime.root.Fields != "") {
		return &commandError{
			Code:     "usage",
			Message:  "--watch cannot be combined with --json or --fields",
			Hint:     "Start without --watch to get one JSON document and return immediately.",
			ExitCode: 2,
		}
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
	if err := runtime.output(result, func() error {
		return writeLines(runtime.stdout,
			fmt.Sprintf("Daylight alarm started, fading over %s.", formatDuration(result.DurationSeconds)),
			"Stop it early with: huerise stop",
		)
	}); err != nil {
		return err
	}
	if !command.Watch {
		return nil
	}
	return watchSunrise(runtime, time.Duration(result.DurationSeconds)*time.Second)
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
		return writeLines(runtime.stdout, "Stopped. The lights stay where they are.")
	})
}
