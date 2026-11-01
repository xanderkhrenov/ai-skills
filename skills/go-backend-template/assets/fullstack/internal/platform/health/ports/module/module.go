// Package module exposes the shared protobuf API for direct in-process calls.
package module

import (
	healthv1 "__MODULE_PATH__/internal/gen/health/v1"
	"__MODULE_PATH__/internal/platform/health"
)

// API is generated from IDL; no separate internal method signatures or DTOs.
type API = healthv1.HealthServiceServer

// New constructs the implementation shared by module, HTTP and gRPC entry points.
func New() API { return health.NewServer() }
