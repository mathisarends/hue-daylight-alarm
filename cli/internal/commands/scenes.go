package commands

import "github.com/mathisarends/huerise/cli/internal/client"

type scenesCommand struct{}

func (scenesCommand) Run(runtime *Runtime) error {
	result, err := fetch[*client.ListRoomsOKApplicationJSON](
		runtime, "list scenes", (*client.Client).ListRooms)
	if err != nil {
		return err
	}
	rooms := []client.RoomResponse(*result)
	return runtime.output(rooms, func() error {
		var rows [][]string
		for _, room := range rooms {
			for _, scene := range room.Scenes {
				rows = append(rows, []string{scene.ID.String(), scene.Name, room.Name})
			}
		}
		return writeTable(runtime.stdout, []string{"ID", "NAME", "ROOM"}, rows, emptyState{
			Message: "No scenes found on the bridge.",
			Hint:    "Create a scene in the Hue app, then run this again.",
		})
	})
}
