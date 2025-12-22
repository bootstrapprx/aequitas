FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY . .

RUN go build -o /out/server ./cmd/server

FROM alpine:3.19

RUN adduser -S -D -H appuser

WORKDIR /home/appuser
COPY --from=builder /out/server /usr/local/bin/server

EXPOSE 8080
USER appuser

ENTRYPOINT ["/usr/local/bin/server"]
