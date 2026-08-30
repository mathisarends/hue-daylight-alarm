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
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.ListHueBridges(runtime.ctx)
	if err != nil {
		return err
	}
	result, ok := response.(*client.ListHueBridgesOKApplicationJSON)
	if !ok {
		return apiFailure("list Hue Bridges", response)
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
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.GetHueBridge(runtime.ctx)
	if err != nil {
		return err
	}
	return handleOnboardingResponse(runtime, "bridge status", response)
}

func (command hueBridgeSelectCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.SelectHueBridge(runtime.ctx, &client.BridgeSelectionRequest{BridgeID: command.BridgeID})
	if err != nil {
		return err
	}
	return handleOnboardingResponse(runtime, "select Hue Bridge", response)
}

func (hueBridgeRegisterCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.RegisterHueBridge(runtime.ctx)
	if err != nil {
		return err
	}
	return handleOnboardingResponse(runtime, "register Hue Bridge", response)
}

func handleOnboardingResponse(runtime *Runtime, operation string, response any) error {
	status, ok := response.(*client.OnboardingStatusResponse)
	if !ok {
		return apiFailure(operation, response)
	}
	return runtime.output(status, func() error {
		return writeRecord(runtime.stdout,
			recordField{Name: "state", Value: string(status.State)},
			recordField{Name: "bridge_id", Value: status.BridgeID.Or("-")},
			recordField{Name: "ip_address", Value: status.IPAddress.Or("-")},
			recordField{Name: "read_only", Value: fmt.Sprintf("%t", status.ReadOnly)},
		)
	})
}
