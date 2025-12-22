package main

import (
	"context"
	"net/http"

	appconfig "aequitas-worker-go/internal/config"
	httpserver "aequitas-worker-go/internal/http"
	"aequitas-worker-go/internal/jobs"
	"aequitas-worker-go/internal/logging"
)

func main() {
	cfg := appconfig.Load()
	logger := logging.NewLogger(cfg.LogLevel, "aequitas-worker-go")
	dispatcher := jobs.NewDispatcher(logger)

	handler := httpserver.NewRouter(logger, dispatcher)

	addr := ":" + cfg.ServicePort
	server := &http.Server{
		Addr:    addr,
		Handler: handler,
	}

	logger.Info(context.Background(), "server_starting", logging.Fields{
		"addr":    addr,
		"loglevel": cfg.LogLevel,
	})

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		logger.Error(context.Background(), "server_error", logging.Fields{"error": err.Error()})
	}
}
