package jobs

import (
	"context"

	"aequitas-worker-go/internal/logging"
)

// Dispatcher is a placeholder for future job orchestration.
type Dispatcher struct {
	logger *logging.Logger
}

// NewDispatcher creates a new Dispatcher instance.
func NewDispatcher(logger *logging.Logger) *Dispatcher {
	return &Dispatcher{logger: logger}
}

// Accept records receipt of a job and returns a generated job id.
func (d *Dispatcher) Accept(ctx context.Context, payload map[string]interface{}) string {
	jobID := logging.GenerateUUID()

	d.logger.Info(ctx, "job_accepted", logging.Fields{
		"job_id": jobID,
		"payload": payload,
	})

	return jobID
}
