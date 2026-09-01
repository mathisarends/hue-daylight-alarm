package commands

import (
	"fmt"
	"io"
	"strings"
	"time"
)

const (
	barWidth   = 24
	framePause = 250 * time.Millisecond
)

// The edge of the bar cycles through these so the line visibly moves even
// while the fade sits on the same percentage for a minute at a time.
var edgeFrames = []string{"░", "▒", "▓", "▒"}

// watchSunrise redraws one line until the fade is over. The alarm runs on the
// server, so leaving early -- by Ctrl-C or by killing the terminal -- only
// stops the watching, never the alarm.
func watchSunrise(runtime *Runtime, duration time.Duration) error {
	if !isTerminal(runtime.stdout) {
		return waitQuietly(runtime, duration)
	}
	started := time.Now()
	ticker := time.NewTicker(framePause)
	defer ticker.Stop()

	for frame := 0; ; frame++ {
		elapsed := time.Since(started)
		if elapsed >= duration {
			return finish(runtime.stdout, duration)
		}
		if err := drawSunrise(runtime.stdout, elapsed, duration, frame); err != nil {
			return err
		}
		select {
		case <-runtime.ctx.Done():
			return interrupted(runtime.stdout)
		case <-ticker.C:
		}
	}
}

func drawSunrise(writer io.Writer, elapsed, duration time.Duration, frame int) error {
	progress := float64(elapsed) / float64(duration)
	filled := int(progress * barWidth)
	bar := strings.Repeat("█", filled)
	if filled < barWidth {
		bar += edgeFrames[frame%len(edgeFrames)] + strings.Repeat("░", barWidth-filled-1)
	}
	line := fmt.Sprintf("%sSunrise  %s  %3.0f%%  %s left",
		indent, bar, progress*100, formatRemaining(duration-elapsed))
	_, err := fmt.Fprintf(writer, "\r%-*s", 60, line)
	return err
}

func finish(writer io.Writer, duration time.Duration) error {
	line := fmt.Sprintf("%sSunrise  %s  100%%  done", indent, strings.Repeat("█", barWidth))
	if _, err := fmt.Fprintf(writer, "\r%-*s\n", 60, line); err != nil {
		return err
	}
	return writeLines(writer, fmt.Sprintf("The %s fade is complete.", formatDuration(int(duration.Seconds()))))
}

func interrupted(writer io.Writer) error {
	if _, err := fmt.Fprintln(writer); err != nil {
		return err
	}
	return writeLines(writer,
		"Stopped watching. The alarm keeps fading.",
		"Cut it short with: huerise stop",
	)
}

func waitQuietly(runtime *Runtime, duration time.Duration) error {
	timer := time.NewTimer(duration)
	defer timer.Stop()
	select {
	case <-runtime.ctx.Done():
		return interrupted(runtime.stdout)
	case <-timer.C:
		return writeLines(runtime.stdout, "The fade is complete.")
	}
}

// formatRemaining keeps the line calm: seconds only matter at the very end.
func formatRemaining(remaining time.Duration) string {
	seconds := int(remaining.Seconds())
	if seconds < 60 {
		return formatDuration(max(seconds, 1))
	}
	return formatDuration((seconds + 59) / 60 * 60)
}
