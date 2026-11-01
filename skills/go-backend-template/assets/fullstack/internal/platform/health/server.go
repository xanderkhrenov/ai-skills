package health

import (
	"context"

	healthv1 "__MODULE_PATH__/internal/gen/health/v1"
)

type Server struct {
	healthv1.UnimplementedHealthServiceServer
}

func NewServer() *Server { return &Server{} }

func (*Server) Check(context.Context, *healthv1.CheckRequest) (*healthv1.CheckResponse, error) {
	return &healthv1.CheckResponse{Status: "serving"}, nil
}
