package commands

import (
	"github.com/mathisarends/huerise/cli/internal/client"
)

type doctorCommand struct{}

func (doctorCommand) Run(runtime *Runtime) error {
	result, err := fetch[*client.DoctorResponse](runtime, "doctor", (*client.Client).Doctor)
	if err != nil {
		return err
	}
	return runtime.output(result, func() error {
		rows := make([][]string, 0, len(result.Checks))
		for _, check := range result.Checks {
			rows = append(rows, []string{check.Name, check.Status})
		}
		return writeTable(runtime.stdout, []string{"CHECK", "STATUS"}, rows, "No checks reported.")
	})
}
