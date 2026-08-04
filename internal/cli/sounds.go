package cli

import (
	"fmt"

	"github.com/google/uuid"
	"github.com/mathisarends/huerise/internal/api"
)

type soundsCommand struct {
	List    soundsListCommand    `cmd:"" help:"List sounds available to alarm profiles."`
	Preview soundsPreviewCommand `cmd:"" help:"Start playback of a sound."`
	Stop    soundsStopCommand    `cmd:"" help:"Stop whatever is currently playing."`
	Volume  soundsVolumeCommand  `cmd:"" help:"Set the playback volume."`
}

type soundsListCommand struct {
	Category string `help:"Filter by sound category (wake_up or get_up)."`
}

type soundsPreviewCommand struct {
	SoundID uuid.UUID `arg:"" name:"sound-id" help:"Sound UUID from sounds list."`
	Volume  int       `help:"Playback volume." default:"60" range:"0..100"`
}

type soundsStopCommand struct{}

type soundsVolumeCommand struct {
	Volume int `arg:"" help:"Playback volume." range:"0..100"`
}

func (command soundsListCommand) Run(runtime *Runtime) error {
	client, err := runtime.client()
	if err != nil {
		return err
	}
	params := api.ListSoundsParams{}
	if command.Category != "" {
		if command.Category != string(api.SoundCategoryWakeUp) && command.Category != string(api.SoundCategoryGetUp) {
			return &commandError{Code: "usage", Message: "--category must be wake_up or get_up", ExitCode: 2}
		}
		params.Category = api.NewOptSoundCategory(api.SoundCategory(command.Category))
	}
	response, err := client.ListSounds(runtime.ctx, params)
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *api.ListSoundsOKApplicationJSON:
		sounds := []api.SoundRead(*result)
		return runtime.output(sounds, func() error {
			rows := make([][]string, 0, len(sounds))
			for _, sound := range sounds {
				rows = append(rows, []string{sound.ID.String(), sound.Name, string(sound.Category)})
			}
			return writeTable(runtime.stdout, []string{"ID", "NAME", "CATEGORY"}, rows, "No sounds found.")
		})
	case *api.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected list sounds response %T", response)
	}
}

func (command soundsPreviewCommand) Run(runtime *Runtime) error {
	if err := validateVolume(command.Volume); err != nil {
		return err
	}
	client, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := client.PreviewSound(runtime.ctx, &api.SoundPreviewRequest{
		SoundID: command.SoundID,
		Volume:  api.NewOptInt(command.Volume),
	})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *api.SoundRead:
		return runtime.output(result, func() error {
			_, err := fmt.Fprintf(runtime.stdout, "Previewing %q at volume %d.\n", result.Name, command.Volume)
			return err
		})
	case *api.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected preview sound response %T", response)
	}
}

func (soundsStopCommand) Run(runtime *Runtime) error {
	client, err := runtime.client()
	if err != nil {
		return err
	}
	if err := client.StopPlayback(runtime.ctx); err != nil {
		return err
	}
	return runtime.output(map[string]any{"stopped": true}, func() error {
		_, err := fmt.Fprintln(runtime.stdout, "Stopped.")
		return err
	})
}

func (command soundsVolumeCommand) Run(runtime *Runtime) error {
	if err := validateVolume(command.Volume); err != nil {
		return err
	}
	client, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := client.SetVolume(runtime.ctx, &api.VolumeRequest{Volume: command.Volume})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *api.SetVolumeNoContent:
		return runtime.output(map[string]any{"volume": command.Volume}, func() error {
			_, err := fmt.Fprintf(runtime.stdout, "Volume set to %d.\n", command.Volume)
			return err
		})
	case *api.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected set volume response %T", response)
	}
}

func validateVolume(volume int) error {
	if volume < 0 || volume > 100 {
		return &commandError{Code: "usage", Message: "volume must be between 0 and 100", ExitCode: 2}
	}
	return nil
}
