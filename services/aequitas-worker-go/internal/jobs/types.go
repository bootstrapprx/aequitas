package jobs

// JobStatus represents the lifecycle state of a job.
type JobStatus string

const (
	StatusAccepted JobStatus = "accepted"
	StatusRunning  JobStatus = "running"
	StatusSucceeded JobStatus = "succeeded"
	StatusFailed    JobStatus = "failed"
)

// JobRequest represents an incoming job request from Python Core.
type JobRequest struct {
	JobType    string                 `json:"job_type"`
	CompanyID  string                 `json:"company_id"`
	Payload    map[string]interface{} `json:"payload"`
	Callback   CallbackConfig         `json:"callback"`
	IdempotencyKey string              `json:"-"` // Set from header
	RequestID      string              `json:"-"` // Set from header
	CorrelationID  string              `json:"-"` // Set from header
}

// CallbackConfig defines how to callback to Python Core.
type CallbackConfig struct {
	URL  string `json:"url"`
	Auth string `json:"auth"`
}

// JobState tracks the runtime state of a job.
type JobState struct {
	JobID         string
	JobType       string
	CompanyID     string
	Status        JobStatus
	RequestID     string
	CorrelationID string
	IdempotencyKey string
	Result        interface{}
	Errors        []JobError
}

// JobError represents a structured error from job execution.
type JobError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// CallbackPayload is the structure sent back to Python Core.
type CallbackPayload struct {
	JobID     string      `json:"job_id"`
	JobType   string      `json:"job_type"`
	CompanyID string      `json:"company_id"`
	Status    JobStatus   `json:"status"`
	Result    interface{} `json:"result"`
	Errors    []JobError  `json:"errors"`
}
