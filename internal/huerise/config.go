package huerise

import (
	"bufio"
	"errors"
	"fmt"
	"os"
	"strings"
)

const DefaultBaseURL = "http://localhost:8000"

type Config struct {
	BaseURL string
	Token   string
}

// LoadConfig reads Huerise settings, using the dotenv file as a fallback.
func LoadConfig(dotEnvPath string) (Config, error) {
	values := map[string]string{}
	if dotEnvPath == "" {
		dotEnvPath = ".env"
	}
	if err := readDotEnv(dotEnvPath, values); err != nil && !errors.Is(err, os.ErrNotExist) {
		return Config{}, err
	}
	get := func(key string) string {
		if value, ok := os.LookupEnv(key); ok {
			return value
		}
		return values[key]
	}
	baseURL := get("HUERISE_API_URL")
	if baseURL == "" {
		baseURL = DefaultBaseURL
	}
	token := get("HUERISE_API_TOKEN")
	if token == "" {
		token = get("API_ACCESS_TOKEN")
	}
	return Config{BaseURL: strings.TrimRight(baseURL, "/"), Token: token}, nil
}

func readDotEnv(path string, values map[string]string) error {
	file, err := os.Open(path)
	if err != nil {
		return err
	}
	defer func() { _ = file.Close() }()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		line = strings.TrimPrefix(line, "export ")
		key, value, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		key, value = strings.TrimSpace(key), strings.TrimSpace(value)
		if len(value) >= 2 && ((value[0] == '"' && value[len(value)-1] == '"') || (value[0] == '\'' && value[len(value)-1] == '\'')) {
			value = value[1 : len(value)-1]
		}
		values[key] = value
	}
	if err := scanner.Err(); err != nil {
		return fmt.Errorf("read %s: %w", path, err)
	}
	return nil
}
