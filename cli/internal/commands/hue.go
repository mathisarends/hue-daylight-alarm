package commands

import (
	"fmt"

	"github.com/mathisarends/huerise/cli/internal/client"
)

type hueCommand struct {
	Bridge hueBridgeCommand `cmd:"" help:"Discover, select, and register a Hue Bridge."`
}

type hueBridgeCommand struct {
	List     hueBridgeListCommand     `cmd:"" help:"List discovered Hue Bridges."`
	Status   hueBridgeStatusCommand   `cmd:"" help:"Show the effective Hue Bridge configuration."`
	Select   hueBridgeSelectCommand   `cmd:"" help:"Select a discovered Hue Bridge."`
	Register hueBridgeRegisterCommand `cmd:"" help:"Register after pressing the bridge link button."`
}

type hueBridgeListCommand struct{}

type hueBridgeStatusCommand struct{}

type hueBridgeSelectCommand struct {
	BridgeID string `arg:"" name:"bridge-id" help:"Stable bridge ID from hue bridge list."`
}

type hueBridgeRegisterCommand struct{}

func (hueBridgeListCommand) Run(runtime *Runtime) error {
	result, err := fetch[*client.ListHueBridgesOKApplicationJSON](
		runtime, "list Hue Bridges", (*client.Client).ListHueBridges)
	if err != nil {
		return err
	}
	bridges := []client.BridgeResponse(*result)
	return runtime.output(bridges, func() error {
		rows := make([][]string, 0, len(bridges))
		for _, bridge := range bridges {
			rows = append(rows, []string{bridge.ID, bridge.IPAddress, fmt.Sprintf("%t", bridge.Selected)})
		}
		return writeTable(runtime.stdout, []string{"ID", "IP ADDRESS", "SELECTED"}, rows, "No Hue Bridges found.")
	})
}

func (hueBridgeStatusCommand) Run(runtime *Runtime) error {
	status, err := fetch[*client.OnboardingStatusResponse](
		runtime, "bridge status", (*client.Client).GetHueBridge)
	if err != nil {
		return err
	}
	return writeOnboardingStatus(runtime, status)
}

func (command hueBridgeSelectCommand) Run(runtime *Runtime) error {
	status, err := send[*client.OnboardingStatusResponse](
		runtime, "select Hue Bridge", (*client.Client).SelectHueBridge,
		&client.BridgeSelectionRequest{BridgeID: command.BridgeID})
	if err != nil {
		return err
	}
	return writeOnboardingStatus(runtime, status)
}

func (hueBridgeRegisterCommand) Run(runtime *Runtime) error {
	status, err := fetch[*client.OnboardingStatusResponse](
		runtime, "register Hue Bridge", (*client.Client).RegisterHueBridge)
	if err != nil {
		return err
	}
	return writeOnboardingStatus(runtime, status)
}

func writeOnboardingStatus(runtime *Runtime, status *client.OnboardingStatusResponse) error {
	return runtime.output(status, func() error {
		return writeRecord(runtime.stdout,
			recordField{Name: "state", Value: string(status.State)},
			recordField{Name: "bridge_id", Value: status.BridgeID.Or("-")},
			recordField{Name: "ip_address", Value: status.IPAddress.Or("-")},
			recordField{Name: "read_only", Value: fmt.Sprintf("%t", status.ReadOnly)},
		)
	})
}
