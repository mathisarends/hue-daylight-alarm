package commands

import (
	"fmt"

	"github.com/google/uuid"
	"github.com/mathisarends/huerise/cli/internal/client"
)

type configurationCommand struct {
	Show configurationShowCommand `cmd:"" default:"withargs" help:"Show the saved configuration."`
	Set  configurationSetCommand  `cmd:"" help:"Save the selected room and scene."`
}

type configurationShowCommand struct{}

func (configurationShowCommand) Run(runtime *Runtime) error {
	result, err := fetch[*client.DaylightAlarmConfigurationResponse](
		runtime, "read configuration", (*client.Client).GetDaylightAlarmConfiguration)
	if err != nil {
		return err
	}
	return runtime.output(result, func() error {
		_, err := fmt.Fprintf(runtime.stdout, "ROOM: %s (%s)\nSCENE: %s (%s)\nBRIGHTNESS: %d → %d\nDURATION: %ds\n", result.Room.Name, result.Room.ID, result.Scene.Name, result.Scene.ID, result.StartBrightness, result.EndBrightness, result.DurationSeconds)
		return err
	})
}

type configurationSetCommand struct {
	RoomID          uuid.UUID  `arg:"" name:"room-id"`
	SceneID         uuid.UUID  `arg:"" name:"scene-id"`
	StartBrightness int        `name:"start-brightness" default:"1"`
	EndBrightness   int        `name:"end-brightness" default:"100"`
	DurationSeconds int        `name:"duration-seconds" default:"1800"`
	AfterRoomID     *uuid.UUID `name:"after-room-id"`
	AfterSceneID    *uuid.UUID `name:"after-scene-id"`
	AfterBrightness *int       `name:"after-brightness"`
	AfterDelay      *int       `name:"after-delay-seconds"`
}

func (command configurationSetCommand) Run(runtime *Runtime) error {
	request := &client.DaylightAlarmConfigurationRequest{
		RoomID: command.RoomID, SceneID: command.SceneID,
		StartBrightness: command.StartBrightness, EndBrightness: command.EndBrightness,
		DurationSeconds: command.DurationSeconds,
	}
	if command.AfterRoomID != nil || command.AfterSceneID != nil || command.AfterBrightness != nil || command.AfterDelay != nil {
		if command.AfterRoomID == nil || command.AfterSceneID == nil || command.AfterBrightness == nil || command.AfterDelay == nil {
			return &commandError{Code: "usage", Message: "after-alarm options must be supplied together", ExitCode: 2}
		}
		request.AfterAlarm = client.NewOptNilAfterAlarmConfigurationRequest(client.AfterAlarmConfigurationRequest{
			RoomID: *command.AfterRoomID, SceneID: *command.AfterSceneID,
			Brightness: *command.AfterBrightness, DelaySeconds: *command.AfterDelay,
		})
	}
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.SetDaylightAlarmConfiguration(runtime.ctx, request)
	if err != nil {
		return err
	}
	result, ok := response.(*client.DaylightAlarmConfigurationResponse)
	if !ok {
		return apiFailure("save configuration", response)
	}
	return runtime.output(result, func() error {
		_, err := fmt.Fprintln(runtime.stdout, "Configuration saved.")
		return err
	})
}
