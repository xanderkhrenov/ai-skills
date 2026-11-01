package http

import (
	"context"
	nethttp "net/http"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"

	healthv1 "__MODULE_PATH__/internal/gen/health/v1"
	healthmodule "__MODULE_PATH__/internal/platform/health/ports/module"
)

// NewHandler maps HTTP onto the same service instance without a gRPC connection.
func NewHandler(ctx context.Context, api healthmodule.API) (nethttp.Handler, error) {
	gateway := runtime.NewServeMux()
	if err := healthv1.RegisterHealthServiceHandlerServer(ctx, gateway, api); err != nil {
		return nil, err
	}
	return gateway, nil
}
