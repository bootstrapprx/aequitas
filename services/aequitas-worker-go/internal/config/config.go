package config

import (
	"fmt"
	"os"
)

// Config holds runtime configuration derived from environment variables.
type Config struct {
	ServicePort string
	LogLevel    string
	QBO         QBOConfig
}

// QBOConfig holds QuickBooks Online integration configuration.
type QBOConfig struct {
	ClientID     string
	ClientSecret string
	Environment  string // "sandbox" or "production"
	BaseURL      string // Optional override
}

// Load reads environment variables and applies defaults.
func Load() Config {
	qboEnv := envOrDefault("QBO_ENV", "sandbox")
	qboBaseURL := os.Getenv("QBO_BASE_URL")

	// Set default base URL if not overridden
	if qboBaseURL == "" {
		if qboEnv == "production" {
			qboBaseURL = "https://quickbooks.api.intuit.com"
		} else {
			qboBaseURL = "https://sandbox-quickbooks.api.intuit.com"
		}
	}

	return Config{
		ServicePort: envOrDefault("SERVICE_PORT", "8080"),
		LogLevel:    envOrDefault("LOG_LEVEL", "info"),
		QBO: QBOConfig{
			ClientID:     os.Getenv("QBO_CLIENT_ID"),
			ClientSecret: os.Getenv("QBO_CLIENT_SECRET"),
			Environment:  qboEnv,
			BaseURL:      qboBaseURL,
		},
	}
}

// ValidateQBO checks if required QBO credentials are present.
func (c *Config) ValidateQBO() error {
	if c.QBO.ClientID == "" {
		return fmt.Errorf("QBO_CLIENT_ID is required")
	}
	if c.QBO.ClientSecret == "" {
		return fmt.Errorf("QBO_CLIENT_SECRET is required")
	}
	return nil
}

func envOrDefault(key, def string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return def
}
