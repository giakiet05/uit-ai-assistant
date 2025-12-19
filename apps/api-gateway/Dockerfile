# Development stage - with Go installed for hot reload
FROM golang:1.25 AS development

WORKDIR /app

# Install air for hot reload (optional)
RUN go install github.com/air-verse/air@latest

# Copy go.mod and go.sum
COPY go.mod go.sum ./
RUN go mod download

# Copy source code (will be overridden by volume in docker-compose)
COPY . .

EXPOSE 8080
CMD ["go", "run", "main.go"]

# Production build stage
FROM golang:1.25 AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN go build -o main .

# Production runtime stage (default)
FROM debian:bookworm-slim AS production

RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/main .

EXPOSE 8080
CMD ["./main"]
