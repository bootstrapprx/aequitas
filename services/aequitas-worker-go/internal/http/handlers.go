package http

import (
	"encoding/json"
	"net/http"

	"aequitas-worker-go/internal/jobs"
	"aequitas-worker-go/internal/logging"
)

const serviceName = "aequitas-worker-go"

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
	var payload map[string]interface{}
	_ = json.NewDecoder(r.Body).Decode(&payload)

	jobID := h.Dispatcher.Accept(r.Context(), payload)

	h.Logger.Info(r.Context(), "job_received", logging.Fields{
		"job_id": jobID,
		"body":   payload,
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
