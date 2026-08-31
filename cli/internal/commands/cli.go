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

const description = `Control the Huerise daylight alarm from the terminal.

Every example below is a full command, including the "huerise" itself.

First run: "huerise bridge list", then "huerise bridge select <id>",
then press the round button on the bridge and run "huerise bridge register".

Then "huerise configuration set" asks which room and scene to wake up to,
"huerise doctor" confirms everything the alarm needs is in place, and
"huerise start --watch" runs it and shows the fade.

Every command prints a readable summary, or stable JSON with --json.`

type commandTree struct {
	JSON    bool   `help:"Emit stable JSON on stdout."`
	Fields  string `help:"Comma-separated top-level fields to include; implies --json." placeholder:"FIELD,..."`
	Compact bool   `help:"Emit compact rather than indented JSON."`
	EnvFile string `help:"Path to a dotenv configuration file." default:".env" type:"path"`
	APIURL  string `name:"api-url" help:"Override HUERISE_API_URL."`
	APIKey  string `name:"api-key" help:"Override HUERISE_API_KEY."`

	Start         startCommand         `cmd:"" help:"Start the daylight alarm."`
	Stop          stopCommand          `cmd:"" help:"Stop a running daylight alarm."`
	Scenes        scenesCommand        `cmd:"" help:"List every Hue scene."`
	Configuration configurationCommand `cmd:"" help:"Read or save the daylight alarm configuration."`
	Bridge        hueBridgeCommand     `cmd:"" help:"Discover, select, and register the Hue Bridge."`

	Doctor  doctorCommand  `cmd:"" help:"Check device configuration."`
	Version versionCommand `cmd:"" help:"Print version information."`
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
		kong.Description(description),
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
	if root.APIKey != "" {
		config.APIKey = root.APIKey
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
