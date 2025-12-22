package config

import "os"

// Config holds runtime configuration derived from environment variables.
type Config struct {
	ServicePort string
	LogLevel    string
}

// Load reads environment variables and applies defaults.
func Load() Config {
	return Config{
		ServicePort: envOrDefault("SERVICE_PORT", "8080"),
		LogLevel:    envOrDefault("LOG_LEVEL", "info"),
	}
}

func envOrDefault(key, def string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return def
}
