package jobs

import (
	"context"
	"fmt"

	"aequitas-worker-go/internal/config"
	"aequitas-worker-go/internal/logging"
	"aequitas-worker-go/internal/qbo"
)

// Executor executes different job types.
type Executor struct {
	logger    *logging.Logger
	config    *config.Config
	qboClient *qbo.Client
}

// NewExecutor creates a new job executor.
func NewExecutor(logger *logging.Logger, cfg *config.Config) *Executor {
	return &Executor{
		logger:    logger,
		config:    cfg,
		qboClient: qbo.NewClient(cfg.QBO, logger),
	}
}

// Execute dispatches the job to the appropriate handler.
func (e *Executor) Execute(ctx context.Context, req JobRequest) (interface{}, error) {
	e.logger.Info(ctx, "executor_start", logging.Fields{
		"job_type": req.JobType,
	})

	switch req.JobType {
	case "qbo.sync_accounts":
		return e.executeQBOSyncAccounts(ctx, req)
	default:
		return nil, fmt.Errorf("unknown job_type: %s", req.JobType)
	}
}

// executeQBOSyncAccounts handles the QuickBooks account sync job.
func (e *Executor) executeQBOSyncAccounts(ctx context.Context, req JobRequest) (interface{}, error) {
	// Validate QBO configuration
	if err := e.config.ValidateQBO(); err != nil {
		return nil, fmt.Errorf("QBO configuration invalid: %w", err)
	}

	// Extract payload parameters
	realmID, ok := req.Payload["realm_id"].(string)
	if !ok || realmID == "" {
		return nil, fmt.Errorf("realm_id is required in payload")
	}

	accessToken, ok := req.Payload["access_token"].(string)
	if !ok || accessToken == "" {
		return nil, fmt.Errorf("access_token is required in payload")
	}

	fullSync := false
	if val, ok := req.Payload["full_sync"].(bool); ok {
		fullSync = val
	}

	// Execute sync
	syncReq := qbo.SyncAccountsRequest{
		RealmID:     realmID,
		AccessToken: accessToken,
		FullSync:    fullSync,
	}

	resp, err := e.qboClient.SyncAccounts(ctx, syncReq)
	if err != nil {
		return nil, fmt.Errorf("QBO sync failed: %w", err)
	}

	// Return result in canonical format
	result := map[string]interface{}{
		"accounts": resp.Accounts,
		"source":   resp.Source,
		"count":    resp.Count,
	}

	e.logger.Info(ctx, "qbo_sync_success", logging.Fields{
		"account_count": resp.Count,
		"realm_id":      realmID,
	})

	return result, nil
}
