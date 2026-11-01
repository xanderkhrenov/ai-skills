package bootstrap

import (
	"context"
	"errors"
	"net"
	"net/http"
	"os"
	"time"

	"google.golang.org/grpc"

	healthv1 "__MODULE_PATH__/internal/gen/health/v1"
	healthhttp "__MODULE_PATH__/internal/platform/health/ports/http"
	healthmodule "__MODULE_PATH__/internal/platform/health/ports/module"
)

type Config struct {
	HTTPAddr string
	GRPCAddr string
}

func ConfigFromEnv() Config {
	return Config{HTTPAddr: env("HTTP_ADDR", ":8080"), GRPCAddr: env("GRPC_ADDR", "127.0.0.1:9090")}
}

func env(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func Run(ctx context.Context, config Config) error {
	httpListener, err := net.Listen("tcp", config.HTTPAddr)
	if err != nil {
		return err
	}
	defer httpListener.Close()
	grpcListener, err := net.Listen("tcp", config.GRPCAddr)
	if err != nil {
		return err
	}
	defer grpcListener.Close()
	return Serve(ctx, httpListener, grpcListener)
}

// Serve shares one service implementation between direct, HTTP and gRPC callers.
func Serve(ctx context.Context, httpListener, grpcListener net.Listener) error {
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	healthAPI := healthmodule.New()
	server := grpc.NewServer()
	healthv1.RegisterHealthServiceServer(server, healthAPI)
	errorsCh := make(chan error, 2)
	go func() { errorsCh <- server.Serve(grpcListener) }()
	defer server.Stop()

	gateway, err := healthhttp.NewHandler(ctx, healthAPI)
	if err != nil {
		return err
	}
	httpServer := &http.Server{Handler: gateway, ReadHeaderTimeout: 5 * time.Second}
	go func() { errorsCh <- httpServer.Serve(httpListener) }()

	var serveErr error
	select {
	case <-ctx.Done():
	case serveErr = <-errorsCh:
	}
	shutdownCtx, stop := context.WithTimeout(context.Background(), 5*time.Second)
	defer stop()
	shutdownErr := httpServer.Shutdown(shutdownCtx)
	if shutdownErr != nil {
		_ = httpServer.Close()
	}
	stopped := make(chan struct{})
	go func() { server.GracefulStop(); close(stopped) }()
	select {
	case <-stopped:
	case <-shutdownCtx.Done():
		server.Stop()
	}
	if errors.Is(serveErr, http.ErrServerClosed) || errors.Is(serveErr, grpc.ErrServerStopped) {
		serveErr = nil
	}
	return errors.Join(serveErr, shutdownErr)
}
