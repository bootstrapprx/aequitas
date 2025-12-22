package jobs

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"aequitas-worker-go/internal/logging"
)

// SendCallback sends job results back to Python Core via HTTP POST.
func SendCallback(
	ctx context.Context,
	logger *logging.Logger,
	callbackURL string,
	payload CallbackPayload,
	requestID string,
	correlationID string,
	idempotencyKey string,
) error {
	logger.Info(ctx, "callback_start", logging.Fields{
		"callback_url": callbackURL,
		"job_id":       payload.JobID,
		"status":       payload.Status,
	})

	// Serialize payload
	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to marshal callback payload: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, "POST", callbackURL, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to create callback request: %w", err)
	}

	// Set canonical headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Aequitas-Request-Id", requestID)
	req.Header.Set("X-Aequitas-Correlation-Id", correlationID)
	if idempotencyKey != "" {
		req.Header.Set("X-Aequitas-Idempotency-Key", idempotencyKey)
	}

	// Execute request with timeout
	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("callback request failed: %w", err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("callback failed with status %d", resp.StatusCode)
	}

	logger.Info(ctx, "callback_success", logging.Fields{
		"callback_url": callbackURL,
		"job_id":       payload.JobID,
		"status_code":  resp.StatusCode,
	})

	return nil
}
