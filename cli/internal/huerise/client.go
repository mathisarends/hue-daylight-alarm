package huerise

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/mathisarends/huerise/cli/internal/client"
)

const defaultTimeout = 65 * time.Second

// refreshMargin refreshes the access token slightly before it actually
// expires, so a request in flight doesn't race the server's clock.
const refreshMargin = 30 * time.Second

type ConfigError struct {
	Message string
	Hint    string
}

func (e *ConfigError) Error() string { return e.Message }

type bearerToken string

func (t bearerToken) AccessToken(context.Context, client.OperationName) (client.AccessToken, error) {
	return client.AccessToken{Token: string(t)}, nil
}

// refreshingToken serves the stored access token, transparently rotating it
// via /auth/refresh once it's within refreshMargin of expiring.
type refreshingToken struct {
	baseURL string
	http    *http.Client
	creds   Credentials
}

func (t *refreshingToken) AccessToken(ctx context.Context, _ client.OperationName) (client.AccessToken, error) {
	if time.Now().Add(refreshMargin).Before(t.creds.ExpiresAt) {
		return client.AccessToken{Token: t.creds.AccessToken}, nil
	}
	refreshed, err := refreshTokenPair(ctx, t.http, t.baseURL, t.creds.RefreshToken)
	if err != nil {
		return client.AccessToken{}, &ConfigError{
			Message: "session expired",
			Hint:    "Run `huerise auth login` again.",
		}
	}
	t.creds = refreshed
	if err := SaveCredentials(refreshed); err != nil {
		return client.AccessToken{}, fmt.Errorf("persist refreshed credentials: %w", err)
	}
	return client.AccessToken{Token: t.creds.AccessToken}, nil
}

func refreshTokenPair(ctx context.Context, httpClient *http.Client, baseURL, refreshToken string) (Credentials, error) {
	payload, err := json.Marshal(map[string]string{"refresh_token": refreshToken})
	if err != nil {
		return Credentials{}, err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, baseURL+"/auth/refresh", bytes.NewReader(payload))
	if err != nil {
		return Credentials{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := httpClient.Do(req)
	if err != nil {
		return Credentials{}, fmt.Errorf("call /auth/refresh: %w", err)
	}
	defer func() { _ = resp.Body.Close() }()
	if resp.StatusCode != http.StatusOK {
		return Credentials{}, fmt.Errorf("refresh rejected with status %d", resp.StatusCode)
	}
	var body struct {
		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
		ExpiresIn    int    `json:"expires_in"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		return Credentials{}, fmt.Errorf("decode refresh response: %w", err)
	}
	return Credentials{
		AccessToken:  body.AccessToken,
		RefreshToken: body.RefreshToken,
		ExpiresAt:    time.Now().Add(time.Duration(body.ExpiresIn) * time.Second),
	}, nil
}

// NewClient constructs the generated client. It authenticates with an
// explicit --token/HUERISE_API_TOKEN override when given, falling back to
// the credentials `huerise auth login` stored locally.
func NewClient(config Config, options ...client.ClientOption) (*client.Client, error) {
	if strings.TrimSpace(config.BaseURL) == "" {
		return nil, &ConfigError{Message: "HUERISE_API_URL is empty"}
	}
	baseURL := strings.TrimRight(config.BaseURL, "/")
	sec, err := securitySource(config, baseURL)
	if err != nil {
		return nil, err
	}
	clientOptions := []client.ClientOption{client.WithClient(&http.Client{Timeout: defaultTimeout})}
	clientOptions = append(clientOptions, options...)
	apiClient, err := client.NewClient(baseURL, sec, clientOptions...)
	if err != nil {
		return nil, fmt.Errorf("configure API client: %w", err)
	}
	return apiClient, nil
}

func securitySource(config Config, baseURL string) (client.SecuritySource, error) {
	if strings.TrimSpace(config.Token) != "" {
		return bearerToken(config.Token), nil
	}
	creds, err := LoadCredentials()
	if err != nil {
		return nil, &ConfigError{
			Message: "not logged in",
			Hint:    "Run `huerise auth login`, or set HUERISE_API_TOKEN.",
		}
	}
	return &refreshingToken{baseURL: baseURL, http: &http.Client{Timeout: defaultTimeout}, creds: creds}, nil
}

// NewUnauthenticatedClient constructs the generated client for the /auth
// endpoints that establish identity in the first place: register, login, and
// logout never consult the security source, so no token is required here.
func NewUnauthenticatedClient(config Config, options ...client.ClientOption) (*client.Client, error) {
	if strings.TrimSpace(config.BaseURL) == "" {
		return nil, &ConfigError{Message: "HUERISE_API_URL is empty"}
	}
	clientOptions := []client.ClientOption{client.WithClient(&http.Client{Timeout: defaultTimeout})}
	clientOptions = append(clientOptions, options...)
	apiClient, err := client.NewClient(strings.TrimRight(config.BaseURL, "/"), bearerToken(""), clientOptions...)
	if err != nil {
		return nil, fmt.Errorf("configure API client: %w", err)
	}
	return apiClient, nil
}
