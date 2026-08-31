package commands

import "github.com/mathisarends/huerise/cli/internal/client"

type scenesCommand struct{}

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
		return writeTable(runtime.stdout, []string{"ID", "NAME", "ROOM"}, rows, emptyState{
			Message: "No scenes found on the bridge.",
			Hint:    "Create a scene in the Hue app, then run this again.",
		})
	})
}
