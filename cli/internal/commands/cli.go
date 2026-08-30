package commands

import (
	"context"
	"fmt"
	"io"
	"strings"

	"github.com/alecthomas/kong"
	"github.com/mathisarends/huerise/cli/internal/client"
	"github.com/mathisarends/huerise/cli/internal/huerise"
)

var Version = "dev"

type commandTree struct {
	JSON    bool   `help:"Emit stable JSON on stdout."`
	Fields  string `help:"Comma-separated top-level fields to include; implies --json." placeholder:"FIELD,..."`
	Compact bool   `help:"Emit compact rather than indented JSON."`
	NoInput bool   `help:"Never prompt; fail with an actionable error instead."`
	EnvFile string `help:"Path to a dotenv configuration file." default:".env" type:"path"`
	APIURL  string `name:"api-url" help:"Override HUERISE_API_URL."`
	Token   string `help:"Override HUERISE_API_TOKEN." hidden:""`

	Auth     authCommand     `cmd:"" help:"Register, log in, and manage local credentials."`
	Rooms    roomsCommand    `cmd:"" help:"Browse rooms and Hue scenes."`
	Hue      hueCommand      `cmd:"" help:"Configure the Hue Bridge."`
	Profiles profilesCommand `cmd:"" help:"Manage alarm profiles."`
	Alarms   alarmsCommand   `cmd:"" help:"Manage sunrise alarms."`
	Doctor   doctorCommand   `cmd:"" help:"Check device configuration."`
	Version  versionCommand  `cmd:"" help:"Print version information."`
}

type versionCommand struct{}

type Runtime struct {
	ctx    context.Context
	root   *commandTree
	config huerise.Config
	stdin  io.Reader
	stdout io.Writer
	stderr io.Writer
}

// Run executes the CLI and returns a process exit code.
func Run(ctx context.Context, args []string, stdin io.Reader, stdout, stderr io.Writer) int {
	if len(args) == 0 {
		args = []string{"--help"}
	}
	if len(args) == 1 && args[0] == "--version" {
		_, _ = fmt.Fprintln(stdout, Version)
		return 0
	}

	var root commandTree
	parser, err := kong.New(
		&root,
		kong.Name("huerise"),
		kong.Description("Control Huerise alarms from the terminal — readable by humans, predictable for agents."),
		kong.UsageOnError(),
		kong.Writers(stdout, stderr),
		kong.Exit(func(code int) { panic(parserExit(code)) }),
	)
	if err != nil {
		return writeError(stderr, false, fmt.Errorf("build command tree: %w", err))
	}
	parsed, exited, err := parseArgs(parser, args)
	if exited >= 0 {
		return exited
	}
	if err != nil {
		return writeError(stderr, wantsJSON(args), &commandError{Code: "usage", Message: err.Error(), ExitCode: 2})
	}

	config, err := huerise.LoadConfig(root.EnvFile)
	if err != nil {
		return writeError(stderr, root.JSON || root.Fields != "", err)
	}
	if root.APIURL != "" {
		config.BaseURL = strings.TrimRight(root.APIURL, "/")
	}
	if root.Token != "" {
		config.Token = root.Token
	}
	runtime := &Runtime{ctx: ctx, root: &root, config: config, stdin: stdin, stdout: stdout, stderr: stderr}
	if err := parsed.Run(runtime); err != nil {
		return writeError(stderr, root.JSON || root.Fields != "", err)
	}
	return 0
}

type parserExit int

func parseArgs(parser *kong.Kong, args []string) (parsed *kong.Context, exitCode int, err error) {
	exitCode = -1
	defer func() {
		if recovered := recover(); recovered != nil {
			if requested, ok := recovered.(parserExit); ok {
				exitCode = int(requested)
				return
			}
			panic(recovered)
		}
	}()
	parsed, err = parser.Parse(args)
	return parsed, exitCode, err
}

func (r *Runtime) client() (*client.Client, error) {
	return huerise.NewClient(r.config)
}

func (r *Runtime) output(value any, human func() error) error {
	return writeOutput(r.stdout, outputOptions{JSON: r.root.JSON, Fields: r.root.Fields, Compact: r.root.Compact}, value, human)
}

func (versionCommand) Run(runtime *Runtime) error {
	return runtime.output(map[string]any{"version": Version}, func() error {
		_, err := fmt.Fprintln(runtime.stdout, Version)
		return err
	})
}

func wantsJSON(args []string) bool {
	for _, arg := range args {
		if arg == "--json" || arg == "--fields" || strings.HasPrefix(arg, "--fields=") {
			return true
		}
	}
	return false
}
