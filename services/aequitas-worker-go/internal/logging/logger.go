package logging

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"time"
)

// Fields represents structured log fields.
type Fields map[string]interface{}

// Level represents a logging level.
type Level int

const (
	LevelDebug Level = iota
	LevelInfo
	LevelError
)

// Logger provides minimal structured logging with JSON output.
type Logger struct {
	level   Level
	service string
	logger  *log.Logger
}

// NewLogger constructs a new Logger with the provided level and service name.
func NewLogger(level, service string) *Logger {
	return &Logger{
		level:   parseLevel(level),
		service: service,
		logger:  log.New(os.Stdout, "", 0),
	}
}

// Info logs an informational message.
func (l *Logger) Info(ctx context.Context, msg string, fields Fields) {
	l.log(ctx, LevelInfo, msg, fields)
}

// Error logs an error message.
func (l *Logger) Error(ctx context.Context, msg string, fields Fields) {
	l.log(ctx, LevelError, msg, fields)
}

func (l *Logger) log(ctx context.Context, level Level, msg string, fields Fields) {
	if level < l.level {
		return
	}

	entry := Fields{
		"timestamp":      time.Now().UTC().Format(time.RFC3339Nano),
		"level":          levelToString(level),
		"message":        msg,
		"service":        l.service,
		"request_id":     requestIDFromContext(ctx),
		"correlation_id": correlationIDFromContext(ctx),
	}

	for k, v := range fields {
		entry[k] = v
	}

	payload, err := json.Marshal(entry)
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to marshal log entry: %v\n", err)
		return
	}

	l.logger.Println(string(payload))
}

func parseLevel(level string) Level {
	switch strings.ToLower(level) {
	case "debug":
		return LevelDebug
	case "error":
		return LevelError
	default:
		return LevelInfo
	}
}

func levelToString(level Level) string {
	switch level {
	case LevelDebug:
		return "debug"
	case LevelError:
		return "error"
	default:
		return "info"
	}
}

type contextKey string

const (
	ctxRequestID     contextKey = "request_id"
	ctxCorrelationID contextKey = "correlation_id"
)

// WithRequestIDs attaches request identifiers to context for downstream logging.
func WithRequestIDs(ctx context.Context, requestID, correlationID string) context.Context {
	ctx = context.WithValue(ctx, ctxRequestID, requestID)
	ctx = context.WithValue(ctx, ctxCorrelationID, correlationID)
	return ctx
}

func requestIDFromContext(ctx context.Context) string {
	if ctx == nil {
		return ""
	}
	if v, ok := ctx.Value(ctxRequestID).(string); ok {
		return v
	}
	return ""
}

func correlationIDFromContext(ctx context.Context) string {
	if ctx == nil {
		return ""
	}
	if v, ok := ctx.Value(ctxCorrelationID).(string); ok {
		return v
	}
	return ""
}

// GenerateUUID returns a RFC 4122 version 4 UUID string.
func GenerateUUID() string {
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		return ""
	}
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	return formatUUID(b)
}

func formatUUID(b []byte) string {
	hexStr := hex.EncodeToString(b)
	return hexStr[0:8] + "-" + hexStr[8:12] + "-" + hexStr[12:16] + "-" + hexStr[16:20] + "-" + hexStr[20:]
}
