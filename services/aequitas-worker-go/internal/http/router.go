package http

import (
	"net/http"

	"aequitas-worker-go/internal/jobs"
	"aequitas-worker-go/internal/logging"
)

// NewRouter constructs the HTTP router with required endpoints and middleware.
func NewRouter(logger *logging.Logger, dispatcher *jobs.Dispatcher) http.Handler {
	handlers := &Handlers{
		Logger:      logger,
		Dispatcher:  dispatcher,
		ServiceName: serviceName,
	}

	mux := http.NewServeMux()
	mux.Handle("/health", http.HandlerFunc(handlers.Health))
	mux.Handle("/jobs", http.HandlerFunc(methodGuard(http.MethodPost, handlers.Jobs)))

	return wrapWithMiddlewares(logger, mux)
}

func methodGuard(method string, handler func(http.ResponseWriter, *http.Request)) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != method {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		handler(w, r)
	}
}
