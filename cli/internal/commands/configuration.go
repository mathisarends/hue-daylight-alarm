package commands

import (
	"errors"
	"fmt"
	"slices"
	"sort"

	"github.com/google/uuid"
	"github.com/mathisarends/huerise/cli/internal/client"
)

const nonInteractiveHint = "Pass room and scene explicitly: huerise configuration set <room-id> <scene-id>"

// errCancelled marks the one outcome that is a decision rather than a failure:
// the user looked at the summary and said no.
var errCancelled = errors.New("cancelled")

type configurationCommand struct {
	Show configurationShowCommand `cmd:"" default:"withargs" help:"Show the saved configuration."`
	Set  configurationSetCommand  `cmd:"" help:"Save the alarm's room, scene, and duration."`
}

type configurationShowCommand struct{}

func (configurationShowCommand) Run(runtime *Runtime) error {
	result, err := fetch[*client.DaylightAlarmConfigurationResponse](
		runtime, "read configuration", (*client.Client).GetDaylightAlarmConfiguration)
	if err != nil {
		return err
	}
	return runtime.output(result, func() error {
		return writeConfiguration(runtime, result)
	})
}

type configurationSetCommand struct {
	RoomID          uuid.UUID  `arg:"" name:"room-id" optional:"" help:"Room to wake up in; asked for when omitted."`
	SceneID         uuid.UUID  `arg:"" name:"scene-id" optional:"" help:"Scene to fade in; asked for when omitted."`
	DurationSeconds int        `name:"duration-seconds" default:"1800"`
	AfterRoomID     *uuid.UUID `name:"after-room-id"`
	AfterSceneID    *uuid.UUID `name:"after-scene-id"`
	AfterDelay      *int       `name:"after-delay-seconds"`
}

func (command configurationSetCommand) Run(runtime *Runtime) error {
	request, err := command.request(runtime)
	if errors.Is(err, errCancelled) {
		return writeLines(runtime.stdout, "Nothing saved.")
	}
	if err != nil {
		return err
	}
	result, err := send[*client.DaylightAlarmConfigurationResponse](
		runtime, "save configuration", (*client.Client).SetDaylightAlarmConfiguration, request)
	if err != nil {
		return err
	}
	return runtime.output(result, func() error {
		if err := writeLines(runtime.stdout, "Configuration saved."); err != nil {
			return err
		}
		if err := writeConfiguration(runtime, result); err != nil {
			return err
		}
		return writeNext(runtime.stdout, "huerise start --watch")
	})
}

func (command configurationSetCommand) request(runtime *Runtime) (*client.DaylightAlarmConfigurationRequest, error) {
	request := &client.DaylightAlarmConfigurationRequest{
		RoomID: command.RoomID, SceneID: command.SceneID,
		DurationSeconds: command.DurationSeconds,
	}
	if err := command.addAfterAlarm(request); err != nil {
		return nil, err
	}
	if request.RoomID != uuid.Nil && request.SceneID != uuid.Nil {
		return request, nil
	}
	if request.RoomID != uuid.Nil || request.SceneID != uuid.Nil {
		return nil, &commandError{
			Code:     "usage",
			Message:  "room-id and scene-id belong together",
			Hint:     nonInteractiveHint,
			ExitCode: 2,
		}
	}
	if runtime.root.JSON || runtime.root.Fields != "" {
		return nil, &commandError{
			Code:     "usage",
			Message:  "room-id and scene-id are required with --json or --fields",
			Hint:     nonInteractiveHint,
			ExitCode: 2,
		}
	}
	return command.askForSelection(runtime, request)
}

func (command configurationSetCommand) addAfterAlarm(request *client.DaylightAlarmConfigurationRequest) error {
	if command.AfterRoomID == nil && command.AfterSceneID == nil && command.AfterDelay == nil {
		return nil
	}
	if command.AfterRoomID == nil || command.AfterSceneID == nil || command.AfterDelay == nil {
		return &commandError{Code: "usage", Message: "after-alarm options must be supplied together", ExitCode: 2}
	}
	request.AfterAlarm = client.NewOptNilAfterAlarmConfigurationRequest(client.AfterAlarmConfigurationRequest{
		RoomID: *command.AfterRoomID, SceneID: *command.AfterSceneID,
		DelaySeconds: *command.AfterDelay,
	})
	return nil
}

func (command configurationSetCommand) askForSelection(
	runtime *Runtime, request *client.DaylightAlarmConfigurationRequest,
) (*client.DaylightAlarmConfigurationRequest, error) {
	result, err := fetch[*client.ListRoomsOKApplicationJSON](
		runtime, "list rooms", (*client.Client).ListRooms)
	if err != nil {
		return nil, err
	}
	rooms := []client.RoomResponse(*result)
	rooms = slices.DeleteFunc(rooms, func(room client.RoomResponse) bool {
		return len(room.Scenes) == 0
	})
	if len(rooms) == 0 {
		return nil, &commandError{
			Code:     "empty",
			Message:  "the bridge reports no scenes",
			Hint:     "Create a scene in the Hue app, then run this again.",
			ExitCode: 1,
		}
	}

	prompt := newPrompter(runtime, nonInteractiveHint)
	roomChoice, err := prompt.selectChoice("Which room?", roomChoices(rooms))
	if err != nil {
		return nil, err
	}
	room := roomByID(rooms, roomChoice.Value.(uuid.UUID))
	scene, err := prompt.selectChoice("Which scene should wake you up?", sceneChoices(room))
	if err != nil {
		return nil, err
	}

	minutes, err := prompt.askInt("Fade duration in minutes", command.DurationSeconds/60, 1, 24*60)
	if err != nil {
		return nil, err
	}

	request.RoomID, request.SceneID = room.ID, scene.Value.(uuid.UUID)
	request.DurationSeconds = minutes * 60

	summary := fmt.Sprintf("Wake up in %s with %q over %s.",
		roomChoice.Label, scene.Label, formatDuration(minutes*60))
	afterwards, err := askAfterAlarm(prompt, room, scene.Value.(uuid.UUID))
	if err != nil {
		return nil, err
	}
	if afterwards != nil {
		request.AfterAlarm = client.NewOptNilAfterAlarmConfigurationRequest(*afterwards)
		summary += fmt.Sprintf(" Then hold %q, %s after it ends.",
			sceneName(room, afterwards.SceneID), formatDuration(afterwards.DelaySeconds))
	}

	if err := writeLines(runtime.stdout, summary); err != nil {
		return nil, err
	}
	confirmed, err := prompt.confirm("Save this", true)
	if err != nil {
		return nil, err
	}
	if !confirmed {
		return nil, errCancelled
	}
	return request, nil
}

// askAfterAlarm offers the scene the room settles into once the fade is over,
// which is the difference between waking up and staying awake in daylight.
// It stays in the alarm's room: nothing else needs waking.
func askAfterAlarm(
	prompt *prompter, room client.RoomResponse, alarmSceneID uuid.UUID,
) (*client.AfterAlarmConfigurationRequest, error) {
	wanted, err := prompt.confirm("Switch to another scene once the fade ends", false)
	if err != nil || !wanted {
		return nil, err
	}
	choices := sceneChoices(room)
	choices = slices.DeleteFunc(choices, func(option choice) bool {
		return option.Value.(uuid.UUID) == alarmSceneID
	})
	scene, err := prompt.selectChoice("Which scene afterwards?", choices)
	if err != nil {
		return nil, err
	}
	delay, err := prompt.askInt("Minutes to wait after the fade", 0, 0, 12*60)
	if err != nil {
		return nil, err
	}
	return &client.AfterAlarmConfigurationRequest{
		RoomID: room.ID, SceneID: scene.Value.(uuid.UUID),
		DelaySeconds: delay * 60,
	}, nil
}

func sceneName(room client.RoomResponse, id uuid.UUID) string {
	for _, scene := range room.Scenes {
		if scene.ID == id {
			return scene.Name
		}
	}
	return id.String()
}

func roomByID(rooms []client.RoomResponse, id uuid.UUID) client.RoomResponse {
	for _, room := range rooms {
		if room.ID == id {
			return room
		}
	}
	return client.RoomResponse{}
}

func roomChoices(rooms []client.RoomResponse) []choice {
	choices := make([]choice, 0, len(rooms))
	for _, room := range rooms {
		choices = append(choices, choice{Label: room.Name, Value: room.ID})
	}
	sort.Slice(choices, func(one, other int) bool { return choices[one].Label < choices[other].Label })
	return choices
}

func sceneChoices(room client.RoomResponse) []choice {
	choices := make([]choice, 0, len(room.Scenes))
	for _, scene := range room.Scenes {
		choices = append(choices, choice{Label: scene.Name, Value: scene.ID})
	}
	sort.Slice(choices, func(one, other int) bool { return choices[one].Label < choices[other].Label })
	return choices
}

func writeConfiguration(runtime *Runtime, config *client.DaylightAlarmConfigurationResponse) error {
	fields := []recordField{
		{Name: "Room", Value: config.Room.Name},
		{Name: "Scene", Value: config.Scene.Name},
		{Name: "Duration", Value: formatDuration(config.DurationSeconds)},
	}
	if after, ok := config.AfterAlarm.Get(); ok {
		fields = append(fields, recordField{
			Name:  "Afterwards",
			Value: fmt.Sprintf("%s, %s later", after.Scene.Name, formatDuration(after.DelaySeconds)),
		})
	}
	return writeRecord(runtime.stdout, fields...)
}
