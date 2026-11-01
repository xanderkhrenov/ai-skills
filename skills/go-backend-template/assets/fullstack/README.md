## Структура и запуск

Backend — Go-модуль в корне; `ui` и `idl` — Git-подмодули. Frontend и backend
собираются и развёртываются отдельно. Контексты лежат в `internal/<context>`:
`domain/<model>`, `usecase/{command,query}`, `ports/{grpc,http,module}`, `adapters/postgres`.

`domain` не зависит от внешних слоёв; `usecase` не импортирует `ports`, `adapters`
и `internal/gen`. Интерфейс репозитория агрегата — в его модели; остальные
интерфейсы зависимостей — рядом с потребителем. Между контекстами — адаптер
потребителя и `ports/module` поставщика. В `ports/module` находится alias
сгенерированного `ServiceServer` и фабрика реализации; вызов идёт напрямую с
protobuf-сообщениями, без сети и отдельного handwritten API.

Единые межконтекстные и сетевые контракты — `idl/proto/__PROJECT_NAME__/<context>/v1/*.proto`, namespace
`__API_NAMESPACE__.<context>.v1`. HTTP-привязки — `google.api.http` в `.proto`.
Генерация: protobuf → Go/gRPC/gateway и OpenAPI 2.0 → TypeScript Fetch-клиент.
Результаты в `internal/gen`, `idl/openapi`, `ui/src/api/generated` коммитятся.
Общая реализация сервисного API преобразует protobuf в вызовы usecase; сетевая
регистрация — через gRPC, прямой доступ — через `ports/module`, HTTP gateway —
через `ports/http`. Bootstrap передаёт один экземпляр всем входам. Health —
техническая реализация в `internal/platform/health`.

Нужны Go __GO_VERSION__, Python 3, Buf и Node версий из `idl/toolchain.json`, npm.
При первом запуске после генерации каркаса:

```sh
npm ci --prefix idl
npm ci --prefix ui
make generate
go mod tidy
make check build
```

Затем в двух терминалах: `make backend-run` и `make ui-dev`.
UI: адрес dev-сервера Vite; `/api/` проксируется на `http://127.0.0.1:8080`
(настройка `API_PROXY_TARGET`). Backend: `HTTP_ADDR=:8080`, `GRPC_ADDR=127.0.0.1:9090`.
HTTP gateway вызывает общую реализацию напрямую через `HandlerServer`, без
gRPC-соединения. Сетевой gRPC-сервер отдельно регистрирует тот же объект.
Прямые вызовы и HTTP gateway обходят gRPC-interceptors: общие проверки должны
быть в реализации/usecase. Адаптеры переводят protobuf и status в бизнес-типы;
`domain`/`usecase` остаются независимыми от protobuf.
`GET /api/v1/health` проверяет доступность процесса, не будущих БД или сервисов.

`make backend-build` не требует UI, `make ui-build` не требует Go;
`make build` собирает оба артефакта. `make generate-check` сравнивает результаты
генерации без изменения файлов. `make check` проверяет Go, TypeScript,
спецификации, совместимость и воспроизводимость генерации. Тесты проверяют
прямой вызов и HTTP handler без сетевых слушателей, а также сетевой gRPC и HTTP.

Внутри версии контракта изменения совместимы; несовместимые получают `v2` рядом
с `v1`. База Buf breaking — `master` в IDL; другую задаёт `IDL_BASE_REF`.
При первой публикации без предыдущих `.proto` проверка совместимости пропускается.
Изменения HTTP-маршрутов и поведения также требуют проверки при ревью.

`make up` собирает и запускает Compose: frontend на `http://localhost:8080`,
`/api/` проксируется в backend; прямые порты backend не публикуются.
`make down` останавливает контейнеры. Генерация и сборка не запускают их.

Миграции добавляются с реализацией в `adapters/postgres/migrations`, технический
код — в `internal/platform/<purpose>`, сквозные тесты — в `tests/`, инфраструктура —
в `deploy/<service>`. Бизнес-логики, БД и CI в каркасе нет.
