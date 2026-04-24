package main

import (
	"bytes"
	"io"
	"log"
	"math/rand"
	"net/http"
	"strconv"
	"time"
)

const simulatedTimeoutDelay = 12 * time.Second

func main() {
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))

	http.HandleFunc("/proxy", func(w http.ResponseWriter, r *http.Request) {
		handleProxy(w, r, rng)
	})

	addr := ":8080"
	log.Printf("network proxy listening on %s", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatalf("proxy server failed: %v", err)
	}
}

func handleProxy(w http.ResponseWriter, r *http.Request, rng *rand.Rand) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	targetURL := r.Header.Get("X-EventRelay-Target-Url")
	if targetURL == "" {
		http.Error(w, "missing X-EventRelay-Target-Url header", http.StatusBadRequest)
		return
	}

	latencyMs := parseHeaderInt(r.Header.Get("X-EventRelay-Latency-Ms"))
	timeoutRate := clampPercent(parseHeaderInt(r.Header.Get("X-EventRelay-Timeout-Rate")))
	failureRate := clampPercent(parseHeaderInt(r.Header.Get("X-EventRelay-Failure-Rate")))

	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "failed to read request body", http.StatusBadRequest)
		return
	}

	if latencyMs > 0 {
		time.Sleep(time.Duration(latencyMs) * time.Millisecond)
	}

	if shouldInject(rng, timeoutRate) {
		log.Printf("proxy target=%s latency_ms=%d injected_timeout=true injected_failure=false", targetURL, latencyMs)
		time.Sleep(simulatedTimeoutDelay)
		http.Error(w, "simulated timeout", http.StatusGatewayTimeout)
		return
	}

	if shouldInject(rng, failureRate) {
		log.Printf("proxy target=%s latency_ms=%d injected_timeout=false injected_failure=true status=503", targetURL, latencyMs)
		http.Error(w, "simulated upstream failure", http.StatusServiceUnavailable)
		return
	}

	req, err := http.NewRequest(http.MethodPost, targetURL, bytes.NewReader(body))
	if err != nil {
		http.Error(w, "invalid target URL", http.StatusBadRequest)
		return
	}

	copyHeaderIfPresent(r.Header, req.Header, "Content-Type")
	copyHeaderIfPresent(r.Header, req.Header, "X-HookHub-Event-Id")
	copyHeaderIfPresent(r.Header, req.Header, "X-HookHub-Timestamp")
	copyHeaderIfPresent(r.Header, req.Header, "X-HookHub-Signature")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		log.Printf("proxy target=%s latency_ms=%d injected_timeout=false injected_failure=false forward_error=%v", targetURL, latencyMs, err)
		http.Error(w, "failed to forward request", http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		http.Error(w, "failed to read upstream response", http.StatusBadGateway)
		return
	}

	for key, values := range resp.Header {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}
	w.WriteHeader(resp.StatusCode)
	_, _ = w.Write(respBody)

	log.Printf(
		"proxy target=%s latency_ms=%d injected_timeout=false injected_failure=false status=%d",
		targetURL,
		latencyMs,
		resp.StatusCode,
	)
}

func parseHeaderInt(value string) int {
	if value == "" {
		return 0
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		return 0
	}
	return parsed
}

func clampPercent(value int) int {
	if value < 0 {
		return 0
	}
	if value > 100 {
		return 100
	}
	return value
}

func shouldInject(rng *rand.Rand, rate int) bool {
	if rate <= 0 {
		return false
	}
	if rate >= 100 {
		return true
	}
	return rng.Intn(100) < rate
}

func copyHeaderIfPresent(src http.Header, dst http.Header, key string) {
	value := src.Get(key)
	if value != "" {
		dst.Set(key, value)
	}
}
