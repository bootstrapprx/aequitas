package http

import (
	"encoding/json"
	"net/http"

	"aequitas-worker-go/internal/jobs"
	"aequitas-worker-go/internal/logging"
)

const serviceName = "aequitas-worker-go"

const (
	headerIdempotencyKey = "X-Aequitas-Idempotency-Key"
)

// Handlers groups HTTP handlers for the service.
type Handlers struct {
	Logger      *logging.Logger
	Dispatcher  *jobs.Dispatcher
	ServiceName string
}

// Health responds with service health.
func (h *Handlers) Health(w http.ResponseWriter, r *http.Request) {
	response := map[string]string{
		"status":  "ok",
		"service": h.ServiceName,
	}
	writeJSON(w, http.StatusOK, response)
}

// Jobs accepts a job request and returns an accepted response with job id.
func (h *Handlers) Jobs(w http.ResponseWriter, r *http.Request) {
	var req jobs.JobRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.Logger.Error(r.Context(), "invalid_job_request", logging.Fields{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "AEQ_JOB_INVALID_REQUEST", "Invalid request payload")
		return
	}

	// Extract request IDs from context (set by middleware)
	req.RequestID = logging.RequestIDFromContext(r.Context())
	req.CorrelationID = logging.CorrelationIDFromContext(r.Context())
	req.IdempotencyKey = r.Header.Get(headerIdempotencyKey)

	// Submit job
	jobID, err := h.Dispatcher.Submit(r.Context(), req)
	if err != nil {
		h.Logger.Error(r.Context(), "job_submit_failed", logging.Fields{
			"error": err.Error(),
		})
		writeError(w, http.StatusBadRequest, "AEQ_JOB_SUBMIT_FAILED", err.Error())
		return
	}

	h.Logger.Info(r.Context(), "job_submitted", logging.Fields{
		"job_id":          jobID,
		"job_type":        req.JobType,
		"company_id":      req.CompanyID,
		"idempotency_key": req.IdempotencyKey,
	})

	response := map[string]interface{}{
		"job_id": jobID,
		"status": "accepted",
	}
	writeJSON(w, http.StatusAccepted, response)
}

func writeJSON(w http.ResponseWriter, status int, body interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

func writeError(w http.ResponseWriter, status int, code, message string) {
	errorResponse := map[string]interface{}{
		"error": map[string]string{
			"code":    code,
			"message": message,
		},
	}
	writeJSON(w, status, errorResponse)
}
