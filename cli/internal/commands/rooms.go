package commands

import (
	"strings"

	"github.com/mathisarends/huerise/cli/internal/client"
)

type roomsCommand struct{}

type scenesCommand struct{}

func (roomsCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.ListRooms(runtime.ctx)
	if err != nil {
		return err
	}
	result, ok := response.(*client.ListRoomsOKApplicationJSON)
	if !ok {
		return apiFailure("list rooms", response)
	}
	rooms := []client.RoomResponse(*result)
	return runtime.output(rooms, func() error {
		rows := make([][]string, 0, len(rooms))
		for _, room := range rooms {
			rows = append(rows, []string{room.ID.String(), room.Name, strings.Join(sceneNames(room.Scenes), ", ")})
		}
		return writeTable(runtime.stdout, []string{"ID", "NAME", "SCENES"}, rows, "No rooms found.")
	})
}

func (scenesCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.ListScenes(runtime.ctx)
	if err != nil {
		return err
	}
	result, ok := response.(*client.ListScenesOKApplicationJSON)
	if !ok {
		return apiFailure("list scenes", response)
	}
	scenes := []client.AvailableSceneResponse(*result)
	return runtime.output(scenes, func() error {
		rows := make([][]string, 0, len(scenes))
		for _, scene := range scenes {
			rows = append(rows, []string{scene.ID.String(), scene.Name, scene.RoomName})
		}
		return writeTable(runtime.stdout, []string{"ID", "NAME", "ROOM"}, rows, "No scenes found.")
	})
}

func sceneNames(scenes []client.SceneResponse) []string {
	names := make([]string, 0, len(scenes))
	for _, scene := range scenes {
		names = append(names, scene.Name)
	}
	return names
}
