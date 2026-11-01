package bootstrap

import (
	"context"
	"io"
	"net"
	"net/http"
	"testing"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"

	healthv1 "__MODULE_PATH__/internal/gen/health/v1"
)

func TestHealthThroughHTTPAndGRPC(t *testing.T) {
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
	connection, err := grpc.NewClient(grpcListener.Addr().String(), grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		t.Fatal(err)
	}
	defer connection.Close()
	rpcContext, stop := context.WithTimeout(ctx, 5*time.Second)
	defer stop()
	want, err := healthv1.NewHealthServiceClient(connection).Check(rpcContext, &healthv1.CheckRequest{}, grpc.WaitForReady(true))
	if err != nil {
		t.Fatal(err)
	}
	client := &http.Client{Timeout: time.Second}
	deadline := time.Now().Add(5 * time.Second)
	for {
		response, err := client.Get("http://" + httpListener.Addr().String() + "/api/v1/health")
		if err == nil {
			body := new(healthv1.CheckResponse)
			payload, readErr := io.ReadAll(response.Body)
			if readErr != nil {
				_ = response.Body.Close()
				t.Fatal(readErr)
			}
			unmarshalErr := protojson.Unmarshal(payload, body)
			_ = response.Body.Close()
			if response.StatusCode == http.StatusOK && unmarshalErr == nil {
				if !proto.Equal(want, body) {
					t.Fatalf("gRPC and HTTP differ: grpc=%v http=%v", want, body)
				}
				return
			}
		}
		if time.Now().After(deadline) {
			t.Fatal("HTTP health did not become available through the direct gateway")
		}
		time.Sleep(10 * time.Millisecond)
	}
}
