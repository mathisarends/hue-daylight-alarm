package commands

import (
	"fmt"
	"strings"

	"github.com/mathisarends/huerise/cli/internal/client"
)

type roomsCommand struct {
	List          roomsListCommand          `cmd:"" help:"List every room Hue knows about."`
	Get           roomsGetCommand           `cmd:"" help:"Show a room and its available scenes."`
	ActivateScene roomsActivateSceneCommand `cmd:"" name:"activate-scene" help:"Preview a scene the way an alarm would start it."`
}

type roomsListCommand struct{}

type roomsGetCommand struct {
	RoomName string `arg:"" name:"room" help:"Hue room name."`
}

type roomsActivateSceneCommand struct {
	RoomName  string `arg:"" name:"room" help:"Hue room name."`
	SceneName string `arg:"" name:"scene" help:"Hue scene name."`
}

func (roomsListCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	rooms, err := apiClient.ListRooms(runtime.ctx)
	if err != nil {
		return err
	}
	return runtime.output(rooms, func() error {
		rows := make([][]string, 0, len(rooms))
		for _, room := range rooms {
			rows = append(rows, []string{room.Name, strings.Join(room.SceneNames, ", ")})
		}
		return writeTable(runtime.stdout, []string{"NAME", "SCENES"}, rows, "No rooms found.")
	})
}

func (command roomsGetCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.GetRoom(runtime.ctx, client.GetRoomParams{RoomName: command.RoomName})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.RoomRead:
		return runtime.output(result, func() error {
			return writeRecord(runtime.stdout,
				recordField{Name: "name", Value: result.Name},
				recordField{Name: "scenes", Value: strings.Join(result.SceneNames, ", ")},
			)
		})
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected get room response %T", response)
	}
}

func (command roomsActivateSceneCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.ActivateScene(runtime.ctx, client.ActivateSceneParams{
		RoomName: command.RoomName, SceneName: command.SceneName,
	})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.ActivateSceneNoContent:
		value := map[string]any{"activated": true, "room_name": command.RoomName, "scene_name": command.SceneName}
		return runtime.output(value, func() error {
			_, err := fmt.Fprintf(runtime.stdout, "Activated %q in %s.\n", command.SceneName, command.RoomName)
			return err
		})
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected activate scene response %T", response)
	}
}
