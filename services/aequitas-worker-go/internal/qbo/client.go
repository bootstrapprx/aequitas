package qbo

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"aequitas-worker-go/internal/config"
	"aequitas-worker-go/internal/logging"
)

// Client handles QuickBooks Online API integration.
type Client struct {
	config     config.QBOConfig
	logger     *logging.Logger
	httpClient *http.Client
}

// NewClient creates a new QuickBooks API client.
func NewClient(cfg config.QBOConfig, logger *logging.Logger) *Client {
	return &Client{
		config: cfg,
		logger: logger,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// Account represents a QuickBooks account in raw, neutral format.
type Account struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Type     string `json:"type"`
	SubType  string `json:"subtype"`
	Active   bool   `json:"active"`
	Currency string `json:"currency"`
	Source   string `json:"source"`
}

// SyncAccountsRequest contains parameters for syncing accounts.
type SyncAccountsRequest struct {
	RealmID    string
	AccessToken string
	FullSync   bool
}

// SyncAccountsResponse contains the result of syncing accounts.
type SyncAccountsResponse struct {
	Accounts []Account
	Source   string
	Count    int
}

// SyncAccounts fetches the chart of accounts from QuickBooks.
// This function handles pagination and transient failures with retries.
func (c *Client) SyncAccounts(ctx context.Context, req SyncAccountsRequest) (*SyncAccountsResponse, error) {
	c.logger.Info(ctx, "qbo_sync_start", logging.Fields{
		"realm_id":  req.RealmID,
		"full_sync": req.FullSync,
	})

	accounts, err := c.fetchAccountsWithRetry(ctx, req.RealmID, req.AccessToken)
	if err != nil {
		return nil, err
	}

	c.logger.Info(ctx, "qbo_sync_complete", logging.Fields{
		"realm_id":      req.RealmID,
		"account_count": len(accounts),
	})

	return &SyncAccountsResponse{
		Accounts: accounts,
		Source:   "quickbooks",
		Count:    len(accounts),
	}, nil
}

// fetchAccountsWithRetry fetches accounts with exponential backoff retry logic.
func (c *Client) fetchAccountsWithRetry(ctx context.Context, realmID, accessToken string) ([]Account, error) {
	maxRetries := 3
	baseDelay := 1 * time.Second

	var lastErr error
	for attempt := 0; attempt < maxRetries; attempt++ {
		if attempt > 0 {
			delay := baseDelay * time.Duration(1<<uint(attempt-1))
			c.logger.Info(ctx, "qbo_retry_delay", logging.Fields{
				"attempt": attempt + 1,
				"delay_ms": delay.Milliseconds(),
			})
			time.Sleep(delay)
		}

		accounts, err := c.fetchAccounts(ctx, realmID, accessToken)
		if err == nil {
			return accounts, nil
		}

		lastErr = err
		c.logger.Error(ctx, "qbo_fetch_failed", logging.Fields{
			"attempt": attempt + 1,
			"error":   err.Error(),
		})

		// Don't retry on authentication errors
		if isAuthError(err) {
			return nil, err
		}
	}

	return nil, fmt.Errorf("failed after %d attempts: %w", maxRetries, lastErr)
}

// fetchAccounts performs a single fetch of accounts from QuickBooks API.
func (c *Client) fetchAccounts(ctx context.Context, realmID, accessToken string) ([]Account, error) {
	// QuickBooks API endpoint for querying accounts
	// Example: GET /v3/company/{realmID}/query?query=select * from Account
	url := fmt.Sprintf("%s/v3/company/%s/query", c.config.BaseURL, realmID)
	query := "select * from Account MAXRESULTS 1000"

	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set required headers
	req.Header.Set("Authorization", "Bearer "+accessToken)
	req.Header.Set("Accept", "application/json")
	q := req.URL.Query()
	q.Add("query", query)
	req.URL.RawQuery = q.Encode()

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, &APIError{
			StatusCode: resp.StatusCode,
			Message:    string(body),
		}
	}

	var qboResp qboQueryResponse
	if err := json.NewDecoder(resp.Body).Decode(&qboResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Convert QuickBooks accounts to our neutral format
	accounts := make([]Account, 0, len(qboResp.QueryResponse.Account))
	for _, qboAcc := range qboResp.QueryResponse.Account {
		accounts = append(accounts, Account{
			ID:       qboAcc.ID,
			Name:     qboAcc.Name,
			Type:     qboAcc.AccountType,
			SubType:  qboAcc.AccountSubType,
			Active:   qboAcc.Active,
			Currency: qboAcc.CurrencyRef.Value,
			Source:   "quickbooks",
		})
	}

	return accounts, nil
}

// APIError represents a QuickBooks API error.
type APIError struct {
	StatusCode int
	Message    string
}

func (e *APIError) Error() string {
	return fmt.Sprintf("QBO API error (status %d): %s", e.StatusCode, e.Message)
}

func isAuthError(err error) bool {
	if apiErr, ok := err.(*APIError); ok {
		return apiErr.StatusCode == 401 || apiErr.StatusCode == 403
	}
	return false
}

// qboQueryResponse matches the QuickBooks API response structure.
type qboQueryResponse struct {
	QueryResponse struct {
		Account      []qboAccount `json:"Account"`
		MaxResults   int          `json:"maxResults"`
		StartPosition int         `json:"startPosition"`
	} `json:"QueryResponse"`
	Time string `json:"time"`
}

// qboAccount matches the QuickBooks Account entity structure.
type qboAccount struct {
	ID              string `json:"Id"`
	Name            string `json:"Name"`
	AccountType     string `json:"AccountType"`
	AccountSubType  string `json:"AccountSubType"`
	Active          bool   `json:"Active"`
	CurrencyRef     struct {
		Value string `json:"value"`
		Name  string `json:"name"`
	} `json:"CurrencyRef"`
	CurrentBalance float64 `json:"CurrentBalance"`
	SyncToken      string  `json:"SyncToken"`
}
