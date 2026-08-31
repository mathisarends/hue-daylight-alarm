package commands

import (
	"bytes"
	"fmt"
	"io"
	"strings"
	"text/tabwriter"
)

// Human output is indented and preceded by a blank line so that a terminal
// full of commands stays readable; --json output is untouched by any of this.
const (
	indent     = "  "
	nextIndent = "        "
)

// emptyState is what a human sees instead of an empty table: the plain fact,
// and the thing worth trying next.
type emptyState struct {
	Message string
	Hint    string
}

func writeTable(writer io.Writer, columns []string, rows [][]string, empty emptyState) error {
	if len(rows) == 0 {
		return writeLines(writer, empty.Message, empty.Hint)
	}
	if _, err := fmt.Fprintln(writer); err != nil {
		return err
	}
	var padded bytes.Buffer
	table := tabwriter.NewWriter(&padded, 0, 4, 2, ' ', 0)
	if len(columns) > 0 {
		if _, err := fmt.Fprintln(table, indent+strings.Join(columns, "\t")); err != nil {
			return err
		}
	}
	for _, row := range rows {
		if _, err := fmt.Fprintln(table, indent+strings.Join(row, "\t")); err != nil {
			return err
		}
	}
	if err := table.Flush(); err != nil {
		return err
	}
	// An empty trailing cell still gets padded, so trim what tabwriter added.
	for line := range strings.Lines(padded.String()) {
		if _, err := fmt.Fprintln(writer, strings.TrimRight(line, " \n")); err != nil {
			return err
		}
	}
	return nil
}

type recordField struct {
	Name  string
	Value string
}

func writeRecord(writer io.Writer, fields ...recordField) error {
	if _, err := fmt.Fprintln(writer); err != nil {
		return err
	}
	table := tabwriter.NewWriter(writer, 0, 4, 2, ' ', 0)
	for _, field := range fields {
		if _, err := fmt.Fprintf(table, "%s%s\t%s\n", indent, field.Name, field.Value); err != nil {
			return err
		}
	}
	return table.Flush()
}

// writeNext prints the commands that move the user forward, aligned under a
// single "Next" label.
func writeNext(writer io.Writer, steps ...string) error {
	if len(steps) == 0 {
		return nil
	}
	if _, err := fmt.Fprintf(writer, "\n%sNext  %s\n", indent, steps[0]); err != nil {
		return err
	}
	for _, step := range steps[1:] {
		if _, err := fmt.Fprintln(writer, nextIndent+step); err != nil {
			return err
		}
	}
	return nil
}

func writeLines(writer io.Writer, lines ...string) error {
	if _, err := fmt.Fprintln(writer); err != nil {
		return err
	}
	for _, line := range lines {
		if line == "" {
			continue
		}
		if _, err := fmt.Fprintln(writer, indent+line); err != nil {
			return err
		}
	}
	return nil
}

func formatDuration(seconds int) string {
	if seconds <= 0 {
		return "0s"
	}
	var parts []string
	for _, unit := range []struct {
		size  int
		label string
	}{{3600, "h"}, {60, "m"}, {1, "s"}} {
		if count := seconds / unit.size; count > 0 {
			parts = append(parts, fmt.Sprintf("%d%s", count, unit.label))
			seconds -= count * unit.size
		}
	}
	return strings.Join(parts, " ")
}
