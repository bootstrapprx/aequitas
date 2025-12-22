package jobs

import (
	"context"
	"fmt"
	"sync"

	"aequitas-worker-go/internal/config"
	"aequitas-worker-go/internal/logging"
)

// Dispatcher manages job execution and lifecycle tracking.
type Dispatcher struct {
	logger   *logging.Logger
	config   *config.Config
	jobs     map[string]*JobState
	jobsMux  sync.RWMutex
	executor *Executor
}

// NewDispatcher creates a new Dispatcher instance.
func NewDispatcher(logger *logging.Logger, cfg *config.Config) *Dispatcher {
	executor := NewExecutor(logger, cfg)
	return &Dispatcher{
		logger:   logger,
		config:   cfg,
		jobs:     make(map[string]*JobState),
		executor: executor,
	}
}

// Submit validates and accepts a job request, then executes it asynchronously.
func (d *Dispatcher) Submit(ctx context.Context, req JobRequest) (string, error) {
	// Validate required fields
	if req.JobType == "" {
		return "", fmt.Errorf("job_type is required")
	}
	if req.CompanyID == "" {
		return "", fmt.Errorf("company_id is required")
	}

	// Generate job ID
	jobID := logging.GenerateUUID()

	// Create job state
	state := &JobState{
		JobID:          jobID,
		JobType:        req.JobType,
		CompanyID:      req.CompanyID,
		Status:         StatusAccepted,
		RequestID:      req.RequestID,
		CorrelationID:  req.CorrelationID,
		IdempotencyKey: req.IdempotencyKey,
		Errors:         []JobError{},
	}

	// Store job state
	d.jobsMux.Lock()
	d.jobs[jobID] = state
	d.jobsMux.Unlock()

	d.logger.Info(ctx, "job_accepted", logging.Fields{
		"job_id":          jobID,
		"job_type":        req.JobType,
		"company_id":      req.CompanyID,
		"idempotency_key": req.IdempotencyKey,
	})

	// Execute asynchronously
	go d.executeJob(req, state)

	return jobID, nil
}

// executeJob runs the job in a goroutine and updates state.
func (d *Dispatcher) executeJob(req JobRequest, state *JobState) {
	// Create new context with IDs for tracing
	ctx := logging.WithRequestIDs(context.Background(), state.RequestID, state.CorrelationID)

	// Update status to running
	d.updateJobStatus(state.JobID, StatusRunning)

	d.logger.Info(ctx, "job_executing", logging.Fields{
		"job_id":   state.JobID,
		"job_type": state.JobType,
	})

	// Execute the job
	result, err := d.executor.Execute(ctx, req)

	if err != nil {
		// Job failed
		d.logger.Error(ctx, "job_failed", logging.Fields{
			"job_id": state.JobID,
			"error":  err.Error(),
		})

		d.jobsMux.Lock()
		state.Status = StatusFailed
		state.Errors = append(state.Errors, JobError{
			Code:    "AEQ_JOB_EXECUTION_FAILED",
			Message: err.Error(),
		})
		d.jobsMux.Unlock()
	} else {
		// Job succeeded
		d.logger.Info(ctx, "job_succeeded", logging.Fields{
			"job_id": state.JobID,
		})

		d.jobsMux.Lock()
		state.Status = StatusSucceeded
		state.Result = result
		d.jobsMux.Unlock()
	}

	// Perform callback if configured
	if req.Callback.URL != "" {
		if err := d.performCallback(ctx, req.Callback, state); err != nil {
			d.logger.Error(ctx, "callback_failed", logging.Fields{
				"job_id": state.JobID,
				"error":  err.Error(),
			})
		}
	}
}

// updateJobStatus updates the status of a job.
func (d *Dispatcher) updateJobStatus(jobID string, status JobStatus) {
	d.jobsMux.Lock()
	defer d.jobsMux.Unlock()

	if state, exists := d.jobs[jobID]; exists {
		state.Status = status
	}
}

// GetJobState retrieves the current state of a job.
func (d *Dispatcher) GetJobState(jobID string) (*JobState, bool) {
	d.jobsMux.RLock()
	defer d.jobsMux.RUnlock()

	state, exists := d.jobs[jobID]
	return state, exists
}

// performCallback sends the job result back to Python Core.
func (d *Dispatcher) performCallback(ctx context.Context, callback CallbackConfig, state *JobState) error {
	payload := CallbackPayload{
		JobID:     state.JobID,
		JobType:   state.JobType,
		CompanyID: state.CompanyID,
		Status:    state.Status,
		Result:    state.Result,
		Errors:    state.Errors,
	}

	return SendCallback(ctx, d.logger, callback.URL, payload, state.RequestID, state.CorrelationID, state.IdempotencyKey)
}
