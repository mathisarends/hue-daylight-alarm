package commands

import (
	"strings"

	"github.com/mathisarends/huerise/cli/internal/client"
)

type hueBridgeCommand struct {
	List     hueBridgeListCommand     `cmd:"" help:"List discovered Hue Bridges."`
	Status   hueBridgeStatusCommand   `cmd:"" help:"Show the effective Hue Bridge configuration."`
	Select   hueBridgeSelectCommand   `cmd:"" help:"Select a discovered Hue Bridge."`
	Register hueBridgeRegisterCommand `cmd:"" help:"Register after pressing the bridge link button."`
}

type hueBridgeListCommand struct{}

type hueBridgeStatusCommand struct{}

type hueBridgeSelectCommand struct {
	BridgeID string `arg:"" name:"bridge-id" help:"Stable bridge ID from huerise bridge list."`
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
			selected := ""
			if bridge.Selected {
				selected = "selected"
			}
			rows = append(rows, []string{bridge.ID, bridge.IPAddress, selected})
		}
		if err := writeTable(runtime.stdout, []string{"ID", "IP ADDRESS", ""}, rows, emptyState{
			Message: "No Hue Bridges found on this network.",
			Hint:    "Check that the bridge is powered on and connected to the same network.",
		}); err != nil {
			return err
		}
		if len(bridges) == 0 {
			return nil
		}
		return writeNext(runtime.stdout, "huerise bridge select <id>")
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
		fields := []recordField{{Name: "State", Value: strings.ReplaceAll(string(status.State), "_", " ")}}
		if bridge := status.BridgeID.Or(""); bridge != "" {
			fields = append(fields, recordField{Name: "Bridge", Value: bridge})
		}
		if address := status.IPAddress.Or(""); address != "" {
			fields = append(fields, recordField{Name: "Address", Value: address})
		}
		if status.ReadOnly {
			fields = append(fields, recordField{Name: "Source", Value: "environment (read-only)"})
		}
		if err := writeRecord(runtime.stdout, fields...); err != nil {
			return err
		}
		return writeNext(runtime.stdout, onboardingNextSteps(status)...)
	})
}

func onboardingNextSteps(status *client.OnboardingStatusResponse) []string {
	switch status.State {
	case client.OnboardingStateNotSelected:
		return []string{"huerise bridge list", "huerise bridge select <id>"}
	case client.OnboardingStateLinkButtonRequired:
		return []string{
			"press the round button on the bridge, then run:",
			"huerise bridge register",
		}
	case client.OnboardingStateReady:
		return []string{"huerise scenes", "huerise doctor"}
	default:
		return nil
	}
}
