package huerise

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/mathisarends/huerise/internal/api"
)

const defaultTimeout = 30 * time.Second

type ConfigError struct {
	Message string
}

func (e *ConfigError) Error() string { return e.Message }

type bearerToken string

func (t bearerToken) AccessToken(context.Context, api.OperationName) (api.AccessToken, error) {
	return api.AccessToken{Token: string(t)}, nil
}

// NewClient constructs the generated client with bearer authentication.
func NewClient(config Config, options ...api.ClientOption) (*api.Client, error) {
	if strings.TrimSpace(config.Token) == "" {
		return nil, &ConfigError{Message: "HUERISE_API_TOKEN is not configured"}
	}
	if strings.TrimSpace(config.BaseURL) == "" {
		return nil, &ConfigError{Message: "HUERISE_API_URL is empty"}
	}
	clientOptions := []api.ClientOption{api.WithClient(&http.Client{Timeout: defaultTimeout})}
	clientOptions = append(clientOptions, options...)
	client, err := api.NewClient(strings.TrimRight(config.BaseURL, "/"), bearerToken(config.Token), clientOptions...)
	if err != nil {
		return nil, fmt.Errorf("configure API client: %w", err)
	}
	return client, nil
}
