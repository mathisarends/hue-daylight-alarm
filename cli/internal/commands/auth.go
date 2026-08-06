package commands

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/mathisarends/huerise/cli/internal/client"
	"github.com/mathisarends/huerise/cli/internal/huerise"
	"golang.org/x/term"
)

type authCommand struct {
	Register authRegisterCommand `cmd:"" help:"Create an account and store its access and refresh tokens."`
	Login    authLoginCommand    `cmd:"" help:"Log in and store its access and refresh tokens."`
	Logout   authLogoutCommand   `cmd:"" help:"Revoke the stored refresh token and forget local credentials."`
}

type authRegisterCommand struct {
	Username string `help:"Account username."`
	Password string `help:"Account password. Prompted for if omitted."`
}

type authLoginCommand struct {
	Username string `help:"Account username."`
	Password string `help:"Account password. Prompted for if omitted."`
}

type authLogoutCommand struct{}

func (command authRegisterCommand) Run(runtime *Runtime) error {
	username, password, err := resolveCredentials(runtime, command.Username, command.Password)
	if err != nil {
		return err
	}
	apiClient, err := huerise.NewUnauthenticatedClient(runtime.config)
	if err != nil {
		return err
	}
	response, err := apiClient.Register(runtime.ctx, &client.RegisterRequest{Username: username, Password: password})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.TokenResponse:
		return storeTokensAndReport(runtime, "Registered and logged in as", username, result)
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected register response %T", response)
	}
}

func (command authLoginCommand) Run(runtime *Runtime) error {
	username, password, err := resolveCredentials(runtime, command.Username, command.Password)
	if err != nil {
		return err
	}
	apiClient, err := huerise.NewUnauthenticatedClient(runtime.config)
	if err != nil {
		return err
	}
	response, err := apiClient.Login(runtime.ctx, &client.LoginRequest{Username: username, Password: password})
	if err != nil {
		return err
	}
	switch result := response.(type) {
	case *client.TokenResponse:
		return storeTokensAndReport(runtime, "Logged in as", username, result)
	case *client.HTTPValidationError:
		return validationError(result)
	default:
		return fmt.Errorf("unexpected login response %T", response)
	}
}

func (authLogoutCommand) Run(runtime *Runtime) error {
	if creds, err := huerise.LoadCredentials(); err == nil && creds.RefreshToken != "" {
		if apiClient, err := huerise.NewUnauthenticatedClient(runtime.config); err == nil {
			// Best-effort: local logout must succeed even if the server is
			// unreachable or the token was already revoked.
			_, _ = apiClient.Logout(runtime.ctx, &client.LogoutRequest{RefreshToken: creds.RefreshToken})
		}
	}
	if err := huerise.ClearCredentials(); err != nil {
		return fmt.Errorf("clear local credentials: %w", err)
	}
	return runtime.output(map[string]any{"logged_out": true}, func() error {
		_, err := fmt.Fprintln(runtime.stdout, "Logged out.")
		return err
	})
}

func storeTokensAndReport(runtime *Runtime, verb, username string, tokens *client.TokenResponse) error {
	creds := huerise.Credentials{
		AccessToken:  tokens.AccessToken,
		RefreshToken: tokens.RefreshToken,
		ExpiresAt:    time.Now().Add(time.Duration(tokens.ExpiresIn) * time.Second),
	}
	if err := huerise.SaveCredentials(creds); err != nil {
		return fmt.Errorf("save credentials: %w", err)
	}
	path, err := huerise.CredentialsPath()
	if err != nil {
		return fmt.Errorf("resolve credentials path: %w", err)
	}
	return runtime.output(map[string]any{"username": username, "expires_in": tokens.ExpiresIn}, func() error {
		_, err := fmt.Fprintf(runtime.stdout, "%s %s. Credentials stored at %s.\n", verb, username, path)
		return err
	})
}

func resolveCredentials(runtime *Runtime, usernameFlag, passwordFlag string) (string, string, error) {
	username, err := resolveUsername(runtime, usernameFlag)
	if err != nil {
		return "", "", err
	}
	password, err := resolvePassword(runtime, passwordFlag)
	if err != nil {
		return "", "", err
	}
	return username, password, nil
}

func resolveUsername(runtime *Runtime, flagValue string) (string, error) {
	if flagValue != "" {
		return flagValue, nil
	}
	if runtime.root.NoInput || !isTerminal(runtime.stdin) {
		return "", &commandError{Code: "input_required", Message: "username is required", Hint: "Pass --username.", ExitCode: 2}
	}
	_, _ = fmt.Fprint(runtime.stderr, "Username: ")
	line, err := bufio.NewReader(runtime.stdin).ReadString('\n')
	if err != nil {
		return "", fmt.Errorf("read username: %w", err)
	}
	username := strings.TrimSpace(line)
	if username == "" {
		return "", &commandError{Code: "input_required", Message: "username is required", ExitCode: 2}
	}
	return username, nil
}

func resolvePassword(runtime *Runtime, flagValue string) (string, error) {
	if flagValue != "" {
		return flagValue, nil
	}
	if runtime.root.NoInput || !isTerminal(runtime.stdin) {
		return "", &commandError{Code: "input_required", Message: "password is required", Hint: "Pass --password.", ExitCode: 2}
	}
	_, _ = fmt.Fprint(runtime.stderr, "Password: ")
	file, ok := runtime.stdin.(*os.File)
	if !ok {
		return "", fmt.Errorf("read password: stdin is not a terminal")
	}
	raw, err := term.ReadPassword(int(file.Fd()))
	_, _ = fmt.Fprintln(runtime.stderr)
	if err != nil {
		return "", fmt.Errorf("read password: %w", err)
	}
	password := strings.TrimSpace(string(raw))
	if password == "" {
		return "", &commandError{Code: "input_required", Message: "password is required", ExitCode: 2}
	}
	return password, nil
}
