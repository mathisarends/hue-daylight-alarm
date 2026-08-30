package huerise

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/mathisarends/huerise/cli/internal/client"
)

const defaultTimeout = 65 * time.Second

type ConfigError struct {
	Message string
	Hint    string
}

func (e *ConfigError) Error() string { return e.Message }

type apiKey string

func (k apiKey) APIKeyHeader(context.Context, client.OperationName) (client.APIKeyHeader, error) {
	return client.APIKeyHeader{APIKey: string(k)}, nil
}

func NewClient(config Config, options ...client.ClientOption) (*client.Client, error) {
	if strings.TrimSpace(config.BaseURL) == "" {
		return nil, &ConfigError{Message: "HUERISE_API_URL is empty"}
	}
	if strings.TrimSpace(config.APIKey) == "" {
		return nil, &ConfigError{
			Message: "HUERISE_API_KEY is empty",
			Hint:    "Set HUERISE_API_KEY in the environment or dotenv file, or pass --api-key.",
		}
	}
	clientOptions := []client.ClientOption{client.WithClient(&http.Client{Timeout: defaultTimeout})}
	clientOptions = append(clientOptions, options...)
	apiClient, err := client.NewClient(strings.TrimRight(config.BaseURL, "/"), apiKey(config.APIKey), clientOptions...)
	if err != nil {
		return nil, fmt.Errorf("configure API client: %w", err)
	}
	return apiClient, nil
}
