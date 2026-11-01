package bootstrap

import (
	"context"
	"encoding/json"
	"net"
	"net/http"
	"testing"
	"time"
)

func TestHealthThroughHTTPGateway(t *testing.T) {
	httpListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = httpListener.Close() })
	grpcListener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = grpcListener.Close() })
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- Serve(ctx, httpListener, grpcListener) }()
	t.Cleanup(func() {
		cancel()
		select {
		case err := <-done:
			if err != nil {
				t.Error(err)
			}
		case <-time.After(7 * time.Second):
			t.Error("backend did not stop")
		}
	})
	client := &http.Client{Timeout: time.Second}
	deadline := time.Now().Add(5 * time.Second)
	for {
		response, err := client.Get("http://" + httpListener.Addr().String() + "/api/v1/health")
		if err == nil {
			var body struct {
				Status string `json:"status"`
			}
			decodeErr := json.NewDecoder(response.Body).Decode(&body)
			_ = response.Body.Close()
			if response.StatusCode == http.StatusOK && decodeErr == nil {
				if body.Status != "serving" {
					t.Fatalf("unexpected health: %q", body.Status)
				}
				return
			}
		}
		if time.Now().After(deadline) {
			t.Fatal("HTTP health did not become available through gRPC gateway")
		}
		time.Sleep(10 * time.Millisecond)
	}
}
