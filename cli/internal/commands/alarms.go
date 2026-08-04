package commands

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/mathisarends/huerise/cli/internal/client"
)

var weekdayNames = []string{"mon", "tue", "wed", "thu", "fri", "sat", "sun"}

type alarmsCommand struct {
	List        alarmsListCommand        `cmd:"" help:"List every alarm."`
	Create      alarmsCreateCommand      `cmd:"" help:"Create a new alarm."`
	Get         alarmsGetCommand         `cmd:"" help:"Show a single alarm."`
	Enable      alarmsEnableCommand      `cmd:"" help:"Enable an alarm."`
	Disable     alarmsDisableCommand     `cmd:"" help:"Disable an alarm."`
	Snooze      alarmsSnoozeCommand      `cmd:"" help:"Snooze the current occurrence."`
	Dismiss     alarmsDismissCommand     `cmd:"" help:"Dismiss the current occurrence."`
	Occurrences alarmsOccurrencesCommand `cmd:"" help:"List recent occurrences."`
	Delete      alarmsDeleteCommand      `cmd:"" help:"Delete an alarm."`
}

type alarmsListCommand struct{}

type alarmsCreateCommand struct {
	Label     string   `arg:"" help:"Human-readable alarm name."`
	Room      string   `required:"" help:"Room to run the sunrise scene in."`
	Hour      int      `required:"" help:"Hour (0-23)."`
	Minute    int      `required:"" help:"Minute (0-59)."`
	Timezone  string   `default:"Europe/Berlin" help:"IANA timezone."`
	Day       []string `help:"Weekday to repeat on; repeat for multiple days (mon-sun)."`
	ProfileID string   `name:"profile-id" help:"Alarm profile UUID; defaults to the default profile."`
}

type alarmsGetCommand struct {
	AlarmID uuid.UUID `arg:"" name:"alarm-id"`
}

type alarmsEnableCommand struct {
	AlarmID uuid.UUID `arg:"" name:"alarm-id"`
}

type alarmsDisableCommand struct {
	AlarmID uuid.UUID `arg:"" name:"alarm-id"`
}

type alarmsSnoozeCommand struct {
	AlarmID uuid.UUID `arg:"" name:"alarm-id"`
	Minutes int       `default:"10" help:"Snooze duration (1-60 minutes)."`
}

type alarmsDismissCommand struct {
	AlarmID uuid.UUID `arg:"" name:"alarm-id"`
}

type alarmsOccurrencesCommand struct {
	AlarmID uuid.UUID `arg:"" name:"alarm-id"`
	Limit   int       `default:"20" help:"Maximum occurrences to return."`
}

type alarmsDeleteCommand struct {
	AlarmID uuid.UUID `arg:"" name:"alarm-id"`
	Yes     bool      `short:"y" help:"Skip confirmation."`
}

func (alarmsListCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	alarms, err := apiClient.ListAlarms(runtime.ctx)
	if err != nil {
		return err
	}
	return runtime.output(alarms, func() error {
		rows := make([][]string, 0, len(alarms))
		for _, alarm := range alarms {
			rows = append(rows, alarmRow(alarm))
		}
		return writeTable(runtime.stdout, []string{"ID", "LABEL", "ROOM", "SCHEDULE", "ENABLED", "NEXT"}, rows, "No alarms yet.")
	})
}

func (command alarmsCreateCommand) Run(runtime *Runtime) error {
	days, err := parseWeekdays(command.Day)
	if err != nil {
		return err
	}
	if command.Hour < 0 || command.Hour > 23 {
		return &commandError{Code: "usage", Message: "hour must be between 0 and 23", ExitCode: 2}
	}
	if command.Minute < 0 || command.Minute > 59 {
		return &commandError{Code: "usage", Message: "minute must be between 0 and 59", ExitCode: 2}
	}
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	room, err := resolveRoom(runtime, apiClient, command.Room)
	if err != nil {
		return err
	}
	request := &client.AlarmCreate{
		Label: command.Label,
		Schedule: client.ScheduleSchema{
			Hour: command.Hour, Minute: command.Minute,
			Timezone: client.NewOptString(command.Timezone), Days: days,
		},
		RoomID:   room.ID,
		RoomName: room.Name,
	}
	if command.ProfileID != "" {
		profileID, parseErr := uuid.Parse(command.ProfileID)
		if parseErr != nil {
			return &commandError{Code: "usage", Message: "invalid --profile-id: " + parseErr.Error(), ExitCode: 2}
		}
		request.ProfileID = client.NewOptNilUUID(profileID)
	}
	response, err := apiClient.CreateAlarm(runtime.ctx, request)
	if err != nil {
		return err
	}
	return handleAlarmResponse(runtime, "create alarm", response)
}

func (command alarmsGetCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.GetAlarm(runtime.ctx, client.GetAlarmParams{AlarmID: command.AlarmID})
	if err != nil {
		return err
	}
	return handleAlarmResponse(runtime, "get alarm", response)
}

func (command alarmsEnableCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.EnableAlarm(runtime.ctx, client.EnableAlarmParams{AlarmID: command.AlarmID})
	if err != nil {
		return err
	}
	return handleAlarmResponse(runtime, "enable alarm", response)
}

func (command alarmsDisableCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.DisableAlarm(runtime.ctx, client.DisableAlarmParams{AlarmID: command.AlarmID})
	if err != nil {
		return err
	}
	return handleAlarmResponse(runtime, "disable alarm", response)
}

func (command alarmsSnoozeCommand) Run(runtime *Runtime) error {
	if command.Minutes < 1 || command.Minutes > 60 {
		return &commandError{Code: "usage", Message: "minutes must be between 1 and 60", ExitCode: 2}
	}
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.SnoozeAlarm(runtime.ctx,
		&client.SnoozeRequest{Minutes: client.NewOptInt(command.Minutes)},
		client.SnoozeAlarmParams{AlarmID: command.AlarmID},
	)
	if err != nil {
		return err
	}
	return handleOccurrenceResponse(runtime, "snooze alarm", response)
}

func (command alarmsDismissCommand) Run(runtime *Runtime) error {
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.DismissAlarm(runtime.ctx, client.DismissAlarmParams{AlarmID: command.AlarmID})
	if err != nil {
		return err
	}
	return handleOccurrenceResponse(runtime, "dismiss alarm", response)
}

func (command alarmsOccurrencesCommand) Run(runtime *Runtime) error {
	if command.Limit < 1 {
		return &commandError{Code: "usage", Message: "limit must be at least 1", ExitCode: 2}
	}
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.ListOccurrences(runtime.ctx, client.ListOccurrencesParams{
		AlarmID: command.AlarmID, Limit: client.NewOptInt(command.Limit),
	})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.ListOccurrencesOKApplicationJSON:
		occurrences := []client.OccurrenceRead(*result)
		return runtime.output(occurrences, func() error {
			rows := make([][]string, 0, len(occurrences))
			for _, occurrence := range occurrences {
				rows = append(rows, occurrenceRow(occurrence))
			}
			return writeTable(runtime.stdout, []string{"ID", "SCHEDULED FOR", "STATE", "SNOOZES", "FAILURE"}, rows, "No occurrences yet.")
		})
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected list occurrences response %T", response)
	}
}

func (command alarmsDeleteCommand) Run(runtime *Runtime) error {
	if !command.Yes {
		if err := confirmDelete(runtime, "alarm", command.AlarmID); err != nil {
			return err
		}
	}
	apiClient, err := runtime.client()
	if err != nil {
		return err
	}
	response, err := apiClient.DeleteAlarm(runtime.ctx, client.DeleteAlarmParams{AlarmID: command.AlarmID})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.DeleteAlarmNoContent:
		return runtime.output(map[string]any{"deleted": true, "id": command.AlarmID.String()}, func() error {
			_, err := fmt.Fprintf(runtime.stdout, "Deleted alarm %s.\n", command.AlarmID)
			return err
		})
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected delete alarm response %T", response)
	}
}

func parseWeekdays(values []string) ([]client.Weekday, error) {
	days := make([]client.Weekday, 0, len(values))
	seen := map[client.Weekday]bool{}
	for _, value := range values {
		index := -1
		for candidate, name := range weekdayNames {
			if strings.EqualFold(value, name) {
				index = candidate
				break
			}
		}
		if index < 0 {
			return nil, &commandError{Code: "usage", Message: fmt.Sprintf("invalid weekday %q", value), Hint: "Choose from: " + strings.Join(weekdayNames, ", "), ExitCode: 2}
		}
		day := client.Weekday(index)
		if !seen[day] {
			days = append(days, day)
			seen[day] = true
		}
	}
	return days, nil
}

func handleAlarmResponse(runtime *Runtime, operation string, response any) error {
	switch result := response.(type) {
	case *client.AlarmRead:
		return writeAlarm(runtime, result)
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected %s response %T", operation, response)
	}
}

func handleOccurrenceResponse(runtime *Runtime, operation string, response any) error {
	switch result := response.(type) {
	case *client.OccurrenceRead:
		return writeOccurrence(runtime, result)
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected %s response %T", operation, response)
	}
}

func writeAlarm(runtime *Runtime, alarm *client.AlarmRead) error {
	return runtime.output(alarm, func() error {
		row := alarmRow(*alarm)
		return writeRecord(runtime.stdout,
			recordField{Name: "id", Value: row[0]},
			recordField{Name: "label", Value: row[1]},
			recordField{Name: "room", Value: row[2]},
			recordField{Name: "schedule", Value: row[3]},
			recordField{Name: "enabled", Value: row[4]},
			recordField{Name: "next", Value: row[5]},
		)
	})
}

func alarmRow(alarm client.AlarmRead) []string {
	next := "-"
	if value, ok := alarm.NextOccurrence.Get(); ok {
		next = value.Format(time.RFC3339)
	}
	return []string{
		alarm.ID.String(), alarm.Label, alarm.RoomName, formatSchedule(alarm.Schedule),
		strconv.FormatBool(alarm.IsEnabled), next,
	}
}

func formatSchedule(schedule client.ScheduleSchema) string {
	value := fmt.Sprintf("%02d:%02d", schedule.Hour, schedule.Minute)
	if len(schedule.Days) == 0 {
		return value + " once"
	}
	days := make([]string, 0, len(schedule.Days))
	for _, day := range schedule.Days {
		index := int(day)
		if index >= 0 && index < len(weekdayNames) {
			days = append(days, weekdayNames[index])
		}
	}
	return value + " " + strings.Join(days, ",")
}

func writeOccurrence(runtime *Runtime, occurrence *client.OccurrenceRead) error {
	return runtime.output(occurrence, func() error {
		row := occurrenceRow(*occurrence)
		return writeRecord(runtime.stdout,
			recordField{Name: "id", Value: row[0]},
			recordField{Name: "scheduled_for", Value: row[1]},
			recordField{Name: "state", Value: row[2]},
			recordField{Name: "snoozes", Value: row[3]},
			recordField{Name: "failure", Value: row[4]},
		)
	})
}

func occurrenceRow(occurrence client.OccurrenceRead) []string {
	return []string{
		occurrence.ID.String(), occurrence.ScheduledFor.Format(time.RFC3339), string(occurrence.State),
		strconv.Itoa(occurrence.SnoozeCount), occurrence.FailureReason.Or("-"),
	}
}

func confirmDelete(runtime *Runtime, resource string, id uuid.UUID) error {
	if runtime.root.NoInput || !isTerminal(runtime.stdin) {
		return &commandError{Code: "input_required", Message: "deleting a " + resource + " requires confirmation", Hint: "Pass --yes to skip confirmation.", ExitCode: 2}
	}
	_, _ = fmt.Fprintf(runtime.stderr, "Delete %s %s? [y/N] ", resource, id)
	answer, err := bufio.NewReader(runtime.stdin).ReadString('\n')
	if err != nil {
		return fmt.Errorf("read confirmation: %w", err)
	}
	answer = strings.TrimSpace(strings.ToLower(answer))
	if answer != "y" && answer != "yes" {
		return &commandError{Code: "cancelled", Message: "delete cancelled", ExitCode: 1}
	}
	return nil
}

func isTerminal(reader any) bool {
	file, ok := reader.(*os.File)
	if !ok {
		return false
	}
	info, err := file.Stat()
	return err == nil && info.Mode()&os.ModeCharDevice != 0
}
