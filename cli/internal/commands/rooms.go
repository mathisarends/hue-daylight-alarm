package commands

import (
	"strings"

	"github.com/mathisarends/huerise/cli/internal/client"
)

type roomsCommand struct{}

type scenesCommand struct{}

func (roomsCommand) Run(runtime *Runtime) error {
	result, err := fetch[*client.ListRoomsOKApplicationJSON](
		runtime, "list rooms", (*client.Client).ListRooms)
	if err != nil {
		return err
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
	result, err := fetch[*client.ListScenesOKApplicationJSON](
		runtime, "list scenes", (*client.Client).ListScenes)
	if err != nil {
		return err
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
