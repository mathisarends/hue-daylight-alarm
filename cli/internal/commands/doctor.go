package commands

import (
	"strings"

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
			rows = append(rows, []string{check.Status, strings.ReplaceAll(check.Name, "_", " ")})
		}
		if err := writeTable(runtime.stdout, nil, rows, emptyState{
			Message: "No checks reported.",
		}); err != nil {
			return err
		}
		if len(rows) == 0 {
			return nil
		}
		return writeLines(runtime.stdout, "Everything the alarm needs is in place.")
	})
}
