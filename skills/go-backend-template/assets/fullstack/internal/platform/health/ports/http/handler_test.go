package http_test

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"

	healthv1 "__MODULE_PATH__/internal/gen/health/v1"
	healthhttp "__MODULE_PATH__/internal/platform/health/ports/http"
	healthmodule "__MODULE_PATH__/internal/platform/health/ports/module"
)

// Neither a gRPC server nor an HTTP listener is started in this test.
func TestModuleAndGatewayUseSameAPIWithoutNetwork(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	api := healthmodule.New()
	want, err := api.Check(ctx, &healthv1.CheckRequest{})
	if err != nil {
		t.Fatal(err)
	}
	if want.GetStatus() != "serving" {
		t.Fatalf("unexpected health: %v", want)
	}
	handler, err := healthhttp.NewHandler(ctx, api)
	if err != nil {
		t.Fatal(err)
	}
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/health", nil).WithContext(ctx))
	if response.Code != http.StatusOK {
		t.Fatalf("unexpected HTTP status %d: %s", response.Code, response.Body.String())
	}
	got := new(healthv1.CheckResponse)
	if err := protojson.Unmarshal(response.Body.Bytes(), got); err != nil {
		t.Fatal(err)
	}
	if !proto.Equal(want, got) {
		t.Fatalf("module and gateway differ: module=%v gateway=%v", want, got)
	}
}
