# Development stage - with Go installed for hot reload
FROM golang:1.25 AS development

WORKDIR /app

# Copy go.mod and go.sum
COPY go.mod go.sum ./
RUN go mod download

# Copy source code (will be overridden by volume in docker-compose)
COPY . .

EXPOSE 8080
# Just use go run - simple and works with volume mount
CMD ["go", "run", "main.go"]

# Production build stage
FROM golang:1.25 AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Build optimized binary (strip debug info, disable CGO)
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o main .

# Production runtime stage (default)
FROM alpine:latest AS production

# Install ca-certificates for HTTPS
RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/main .

EXPOSE 8080
CMD ["./main"]
