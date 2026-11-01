.DEFAULT_GOAL := build

.PHONY: build backend-build ui-build backend-run ui-dev generate generate-check contract-check fmt fmt-check vet test ui-check check up down docker-build

build: backend-build ui-build

backend-build:
	mkdir -p bin
	go build -o bin/__PROJECT_NAME__ ./cmd/__PROJECT_NAME__

ui-build:
	npm --prefix ui run build

backend-run:
	go run ./cmd/__PROJECT_NAME__

ui-dev:
	npm --prefix ui run dev

generate:
	python3 idl/scripts/contracts.py generate

generate-check:
	python3 idl/scripts/contracts.py check

contract-check:
	cd idl && buf lint
	python3 idl/scripts/contracts.py breaking

fmt:
	gofmt -w cmd internal

fmt-check:
	@files="$$(gofmt -l cmd internal)" || exit $$?; \
	if [ -n "$$files" ]; then printf 'Run make fmt for:\n%s\n' "$$files"; exit 1; fi

vet:
	go vet ./cmd/... ./internal/...

test:
	go test ./cmd/... ./internal/...

ui-check:
	npm --prefix ui run check

check: fmt-check vet test ui-check contract-check generate-check

docker-build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down
