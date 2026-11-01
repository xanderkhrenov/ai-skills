package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"__MODULE_PATH__/internal/bootstrap"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	if err := bootstrap.Run(ctx, bootstrap.ConfigFromEnv()); err != nil {
		log.Fatal(err)
	}
}
