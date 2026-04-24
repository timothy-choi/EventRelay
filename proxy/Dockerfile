FROM golang:1.22-alpine AS builder

WORKDIR /src
COPY proxy/main.go /src/main.go
RUN go build -o /proxy main.go

FROM alpine:3.20

WORKDIR /app
COPY --from=builder /proxy /usr/local/bin/proxy

EXPOSE 8080

CMD ["proxy"]
