package commands

import (
	"github.com/mathisarends/huerise/cli/internal/client"
)

type doctorCommand struct{}

func (doctorCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.Doctor(runtime.ctx)
	if err != nil {
		return err
	}
	result, ok := response.(*client.DoctorResponse)
	if !ok {
		return apiFailure("doctor", response)
	}
	return runtime.output(result, func() error {
		rows := make([][]string, 0, len(result.Checks))
		for _, check := range result.Checks {
			rows = append(rows, []string{check.Name, check.Status})
		}
		return writeTable(runtime.stdout, []string{"CHECK", "STATUS"}, rows, "No checks reported.")
	})
}
