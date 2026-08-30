package commands

import (
	"fmt"

	"github.com/mathisarends/huerise/cli/internal/client"
)

type doctorCommand struct{}

func (doctorCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	result, err := apiClient.Doctor(runtime.ctx)
	if err != nil {
		return err
	}
	return writeDoctor(runtime, result)
}

func writeDoctor(runtime *Runtime, result *client.DoctorRead) error {
	return runtime.output(result, func() error {
		return writeRecord(runtime.stdout,
			recordField{Name: "configured", Value: fmt.Sprintf("%t", result.Configured)},
			recordField{Name: "hue_bridge", Value: fmt.Sprintf("%t", result.HueBridge.Configured)},
		)
	})
}
