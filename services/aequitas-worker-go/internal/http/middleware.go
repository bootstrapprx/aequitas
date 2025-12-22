package http

import (
	"net/http"
	"time"

	"aequitas-worker-go/internal/logging"
)

const (
	headerRequestID     = "X-Aequitas-Request-Id"
	headerCorrelationID = "X-Aequitas-Correlation-Id"
	headerIdempotency   = "X-Aequitas-Idempotency-Key"
)

type responseWriter struct {
	http.ResponseWriter
	status int
}

func (rw *responseWriter) WriteHeader(statusCode int) {
	rw.status = statusCode
	rw.ResponseWriter.WriteHeader(statusCode)
}

func wrapWithMiddlewares(logger *logging.Logger, handler http.Handler) http.Handler {
	withContext := requestContextMiddleware(handler)
	withLogging := loggingMiddleware(logger, withContext)
	return withLogging
}

func requestContextMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		reqID := r.Header.Get(headerRequestID)
		if reqID == "" {
			reqID = logging.GenerateUUID()
		}

		corrID := r.Header.Get(headerCorrelationID)
		if corrID == "" {
			corrID = logging.GenerateUUID()
		}

		w.Header().Set(headerRequestID, reqID)
		w.Header().Set(headerCorrelationID, corrID)

		ctx := logging.WithRequestIDs(r.Context(), reqID, corrID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func loggingMiddleware(logger *logging.Logger, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		lrw := &responseWriter{ResponseWriter: w, status: http.StatusOK}

		next.ServeHTTP(lrw, r)

		duration := time.Since(start).Milliseconds()
		logger.Info(r.Context(), "http_request", logging.Fields{
			"method":       r.Method,
			"path":         r.URL.Path,
			"status_code":  lrw.status,
			"duration_ms":  duration,
			"idempotency":  r.Header.Get(headerIdempotency),
		"content_type": r.Header.Get("Content-Type"),
	})
})
}
