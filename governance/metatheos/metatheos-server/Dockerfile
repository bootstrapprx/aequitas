# Build Stage
FROM rust:latest as builder

RUN apt-get update && apt-get install -y clang libclang-dev

WORKDIR /app

# Create separate cargo workspace for caching
COPY Cargo.toml Cargo.lock ./
COPY metatheos-core ./metatheos-core
COPY metatheos-cli ./metatheos-cli
COPY metatheos-server ./metatheos-server
COPY metatheos-gui/src-tauri ./metatheos-gui/src-tauri

# We only need to build metatheos-server
WORKDIR /app/metatheos-server
RUN cargo build --release

# Runtime Stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y openssl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/target/release/metatheos-server /app/metatheos-server

# Expose port
EXPOSE 3000

CMD ["./metatheos-server"]
