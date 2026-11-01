.DEFAULT_GOAL := build

.PHONY: build run fmt fmt-check test vet check docker-build up down

build:
	mkdir -p bin
	go build -o bin/__PROJECT_NAME__ ./cmd/__PROJECT_NAME__

run:
	go run ./cmd/__PROJECT_NAME__

fmt:
	go fmt ./...

fmt-check:
	@files="$$(gofmt -l .)" || exit $$?; \
	if [ -n "$$files" ]; then \
		printf 'Run make fmt for:\n%s\n' "$$files"; \
		exit 1; \
	fi

test:
	go test ./...

vet:
	go vet ./...

check: fmt-check vet test

docker-build:
	docker build -t __PROJECT_NAME__:local .

up:
	docker compose up --build

down:
	docker compose down
