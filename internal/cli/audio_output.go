package cli

import (
	"fmt"
	"strings"

	"github.com/mathisarends/huerise/internal/api"
)

type audioOutputCommand struct {
	Get    audioOutputGetCommand    `cmd:"" help:"Show the current playback output."`
	Select audioOutputSelectCommand `cmd:"" help:"Switch playback to another output."`
}

type audioOutputGetCommand struct{}

type audioOutputSelectCommand struct {
	Output string `arg:"" help:"Output to select." enum:"local,sonos"`
}

func (audioOutputGetCommand) Run(runtime *Runtime) error {
	client, err := runtime.client()
	if err != nil {
		return err
	}
	status, err := client.GetAudioOutput(runtime.ctx)
	if err != nil {
		return err
	}
	return writeAudioOutput(runtime, status)
}

func (command audioOutputSelectCommand) Run(runtime *Runtime) error {
	client, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := client.SelectAudioOutput(runtime.ctx, &api.AudioOutputRequest{Output: api.AudioOutput(command.Output)})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *api.AudioOutputRead:
		return writeAudioOutput(runtime, result)
	case *api.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected select audio output response %T", response)
	}
}

func writeAudioOutput(runtime *Runtime, status *api.AudioOutputRead) error {
	return runtime.output(status, func() error {
		available := make([]string, 0, len(status.Available))
		for _, output := range status.Available {
			available = append(available, string(output))
		}
		return writeRecord(runtime.stdout,
			recordField{Name: "active", Value: string(status.Active)},
			recordField{Name: "available", Value: strings.Join(available, ", ")},
		)
	})
}
