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
	Demo          roomsDemoCommand          `cmd:"" help:"Fast-forward a whole sunrise on a scene, lights only."`
	StopDemo      roomsStopDemoCommand      `cmd:"" name:"stop-demo" help:"Cut a running demo short."`
}

type roomsListCommand struct{}

type roomsGetCommand struct {
	RoomName string `arg:"" name:"room" help:"Hue room name."`
}

type roomsActivateSceneCommand struct {
	RoomName   string   `arg:"" name:"room" help:"Hue room name."`
	SceneName  string   `arg:"" name:"scene" help:"Hue scene name."`
	Brightness *float64 `help:"Override the scene's brightness (0-100)."`
}

type roomsDemoCommand struct {
	RoomName        string   `arg:"" name:"room" help:"Hue room name."`
	SceneName       string   `arg:"" name:"scene" help:"Hue scene name."`
	DurationSeconds *float64 `name:"duration-seconds" help:"How long the whole climb should take (0-300s, default 20)."`
	BrightnessStart *int     `name:"brightness-start" help:"Starting brightness (1-100, default 1)."`
	BrightnessEnd   *int     `name:"brightness-end" help:"Ending brightness (1-100, default 100)."`
}

type roomsStopDemoCommand struct {
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
			rows = append(rows, []string{room.Name, strings.Join(sceneNames(room.Scenes), ", ")})
		}
		return writeTable(runtime.stdout, []string{"NAME", "SCENES"}, rows, "No rooms found.")
	})
}

func (command roomsGetCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	room, err := resolveRoom(runtime, apiClient, command.RoomName)
	if err != nil {
		return err
	}
	return runtime.output(room, func() error {
		return writeRecord(runtime.stdout,
			recordField{Name: "name", Value: room.Name},
			recordField{Name: "scenes", Value: strings.Join(sceneNames(room.Scenes), ", ")},
		)
	})
}

func (command roomsActivateSceneCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	room, scene, err := resolveRoomAndScene(runtime, apiClient, command.RoomName, command.SceneName)
	if err != nil {
		return err
	}
	body := client.OptNilSceneActivationRequest{}
	if command.Brightness != nil {
		body = client.NewOptNilSceneActivationRequest(client.SceneActivationRequest{
			Brightness: client.NewOptNilFloat64(*command.Brightness),
		})
	}
	response, err := apiClient.ActivateScene(runtime.ctx, body, client.ActivateSceneParams{
		RoomID: room.ID, SceneID: scene.ID,
	})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.ActivateSceneNoContent:
		value := map[string]any{"activated": true, "room_name": room.Name, "scene_name": scene.Name}
		return runtime.output(value, func() error {
			_, err := fmt.Fprintf(runtime.stdout, "Activated %q in %s.\n", scene.Name, room.Name)
			return err
		})
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected activate scene response %T", response)
	}
}

func (command roomsDemoCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	room, scene, err := resolveRoomAndScene(runtime, apiClient, command.RoomName, command.SceneName)
	if err != nil {
		return err
	}
	request := client.SunriseDemoRequest{}
	if command.DurationSeconds != nil {
		request.DurationSeconds = client.NewOptFloat64(*command.DurationSeconds)
	}
	if command.BrightnessStart != nil {
		request.BrightnessStart = client.NewOptInt(*command.BrightnessStart)
	}
	if command.BrightnessEnd != nil {
		request.BrightnessEnd = client.NewOptInt(*command.BrightnessEnd)
	}
	response, err := apiClient.DemoScene(runtime.ctx,
		client.NewOptNilSunriseDemoRequest(request),
		client.DemoSceneParams{RoomID: room.ID, SceneID: scene.ID},
	)
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.SunriseDemoRead:
		return writeDemo(runtime, result)
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected demo scene response %T", response)
	}
}

func (command roomsStopDemoCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	room, scene, err := resolveRoomAndScene(runtime, apiClient, command.RoomName, command.SceneName)
	if err != nil {
		return err
	}
	response, err := apiClient.StopSceneDemo(runtime.ctx, client.StopSceneDemoParams{RoomID: room.ID, SceneID: scene.ID})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.StopSceneDemoNoContent:
		return runtime.output(map[string]any{"stopped": true}, func() error {
			_, err := fmt.Fprintln(runtime.stdout, "Stopped.")
			return err
		})
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected stop scene demo response %T", response)
	}
}

func writeDemo(runtime *Runtime, demo *client.SunriseDemoRead) error {
	return runtime.output(demo, func() error {
		return writeRecord(runtime.stdout,
			recordField{Name: "room", Value: demo.RoomName},
			recordField{Name: "scene", Value: demo.SceneName},
			recordField{Name: "brightness_start", Value: fmt.Sprintf("%d", demo.BrightnessStart)},
			recordField{Name: "brightness_end", Value: fmt.Sprintf("%d", demo.BrightnessEnd)},
			recordField{Name: "steps", Value: fmt.Sprintf("%d", demo.Steps)},
			recordField{Name: "step_interval_seconds", Value: fmt.Sprintf("%g", demo.StepIntervalSeconds)},
			recordField{Name: "duration_seconds", Value: fmt.Sprintf("%g", demo.DurationSeconds)},
		)
	})
}

func sceneNames(scenes []client.SceneRead) []string {
	names := make([]string, 0, len(scenes))
	for _, scene := range scenes {
		names = append(names, scene.Name)
	}
	return names
}

func resolveRoom(runtime *Runtime, apiClient *client.Client, roomName string) (*client.RoomRead, error) {
	rooms, err := apiClient.ListRooms(runtime.ctx)
	if err != nil {
		return nil, err
	}
	for _, room := range rooms {
		if strings.EqualFold(room.Name, roomName) {
			return &room, nil
		}
	}
	return nil, &commandError{Code: "usage", Message: fmt.Sprintf("no room named %q", roomName), ExitCode: 2}
}

func resolveRoomAndScene(runtime *Runtime, apiClient *client.Client, roomName, sceneName string) (*client.RoomRead, *client.SceneRead, error) {
	room, err := resolveRoom(runtime, apiClient, roomName)
	if err != nil {
		return nil, nil, err
	}
	for _, scene := range room.Scenes {
		if strings.EqualFold(scene.Name, sceneName) {
			return room, &scene, nil
		}
	}
	return nil, nil, &commandError{Code: "usage", Message: fmt.Sprintf("no scene named %q in room %q", sceneName, roomName), ExitCode: 2}
}
