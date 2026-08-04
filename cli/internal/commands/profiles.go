package commands

import (
	"fmt"
	"strconv"

	"github.com/google/uuid"
	"github.com/mathisarends/huerise/cli/internal/client"
)

type profilesCommand struct {
	List   profilesListCommand   `cmd:"" help:"List every alarm profile."`
	Create profilesCreateCommand `cmd:"" help:"Create a new alarm profile."`
	Delete profilesDeleteCommand `cmd:"" help:"Delete an alarm profile."`
}

type profilesListCommand struct{}

type profilesCreateCommand struct {
	Name            string    `arg:"" help:"Human-readable profile name."`
	Room            string    `required:"" help:"Room the sunrise scene lives in."`
	IntroSoundID    uuid.UUID `name:"intro-sound-id" required:"" help:"Sound UUID from sounds list."`
	RingtoneSoundID uuid.UUID `name:"ringtone-sound-id" required:"" help:"Sound UUID from sounds list."`
	RingtoneVolume  int       `default:"80" help:"Ringtone volume (0-100)."`
	SceneName       string    `default:"Tageslichtwecker" help:"Hue scene name."`
	DurationMinutes int       `default:"7" help:"Sunrise duration (0-120 minutes)."`
	BrightnessStart int       `default:"1" help:"Starting brightness (1-99)."`
	BrightnessEnd   int       `default:"100" help:"Ending brightness (2-100)."`
}

type profilesDeleteCommand struct {
	ProfileID uuid.UUID `arg:"" name:"profile-id"`
	Yes       bool      `short:"y" help:"Skip confirmation."`
}

func (profilesListCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	profiles, err := apiClient.ListProfiles(runtime.ctx)
	if err != nil {
		return err
	}
	return runtime.output(profiles, func() error {
		rows := make([][]string, 0, len(profiles))
		for _, profile := range profiles {
			rows = append(rows, profileRow(profile))
		}
		return writeTable(runtime.stdout, []string{"ID", "NAME", "DEFAULT", "SCENE", "INTRO SOUND", "RINGTONE SOUND"}, rows, "No profiles yet.")
	})
}

func (command profilesCreateCommand) Run(runtime *Runtime) error {
	if err := command.validate(); err != nil {
		return err
	}
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	_, scene, err := resolveRoomAndScene(runtime, apiClient, command.Room, command.SceneName)
	if err != nil {
		return err
	}
	request := &client.ProfileCreate{
		Name:  command.Name,
		Intro: client.IntroSchema{SoundID: command.IntroSoundID},
		Ringtone: client.RingtoneSchema{
			SoundID: command.RingtoneSoundID,
			Volume:  client.NewOptInt(command.RingtoneVolume),
		},
		Sunrise: client.SunriseSchema{
			SceneID:         scene.ID,
			SceneName:       scene.Name,
			DurationMinutes: client.NewOptInt(command.DurationMinutes),
			BrightnessStart: client.NewOptInt(command.BrightnessStart),
			BrightnessEnd:   client.NewOptInt(command.BrightnessEnd),
		},
	}
	response, err := apiClient.CreateProfile(runtime.ctx, request)
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.ProfileRead:
		return writeProfile(runtime, result)
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected create profile response %T", response)
	}
}

func (command profilesCreateCommand) validate() error {
	if err := validateVolume(command.RingtoneVolume); err != nil {
		return err
	}
	if command.DurationMinutes < 0 || command.DurationMinutes > 120 {
		return &commandError{Code: "usage", Message: "duration must be between 0 and 120 minutes", ExitCode: 2}
	}
	if command.BrightnessStart < 1 || command.BrightnessStart > 99 {
		return &commandError{Code: "usage", Message: "starting brightness must be between 1 and 99", ExitCode: 2}
	}
	if command.BrightnessEnd < 2 || command.BrightnessEnd > 100 {
		return &commandError{Code: "usage", Message: "ending brightness must be between 2 and 100", ExitCode: 2}
	}
	if command.BrightnessStart >= command.BrightnessEnd {
		return &commandError{Code: "usage", Message: "starting brightness must be less than ending brightness", ExitCode: 2}
	}
	return nil
}

func (command profilesDeleteCommand) Run(runtime *Runtime) error {
	if !command.Yes {
		if err := confirmDelete(runtime, "profile", command.ProfileID); err != nil {
			return err
		}
	}
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.DeleteProfile(runtime.ctx, client.DeleteProfileParams{ProfileID: command.ProfileID})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.DeleteProfileNoContent:
		return runtime.output(map[string]any{"deleted": true, "id": command.ProfileID.String()}, func() error {
			_, err := fmt.Fprintf(runtime.stdout, "Deleted profile %s.\n", command.ProfileID)
			return err
		})
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected delete profile response %T", response)
	}
}

func writeProfile(runtime *Runtime, profile *client.ProfileRead) error {
	return runtime.output(profile, func() error {
		row := profileRow(*profile)
		return writeRecord(runtime.stdout,
			recordField{Name: "id", Value: row[0]},
			recordField{Name: "name", Value: row[1]},
			recordField{Name: "default", Value: row[2]},
			recordField{Name: "scene", Value: row[3]},
			recordField{Name: "intro_sound", Value: row[4]},
			recordField{Name: "ringtone_sound", Value: row[5]},
		)
	})
}

func profileRow(profile client.ProfileRead) []string {
	return []string{
		profile.ID.String(),
		profile.Name,
		strconv.FormatBool(profile.IsDefault),
		profile.Sunrise.SceneName,
		profile.Intro.SoundID.String(),
		profile.Ringtone.SoundID.String(),
	}
}
