package main

import (
	"context"
	"os"
	"os/signal"

	"github.com/mathisarends/huerise/internal/cli"
)

var version = "dev"

func main() {
	cli.Version = version
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	os.Exit(cli.Run(ctx, os.Args[1:], os.Stdin, os.Stdout, os.Stderr))
}
