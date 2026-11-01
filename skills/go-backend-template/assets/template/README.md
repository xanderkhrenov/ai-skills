# __PROJECT_NAME__

Шаблон Go backend: модульный монолит с DDD и Clean Architecture в стиле
[ThreeDotsLabs](https://threedots.tech/post/introducing-clean-architecture/).
Go __GO_VERSION__. Бизнес-логики и серверов пока нет: запуск сразу завершается.

```text
cmd/__PROJECT_NAME__/main.go
internal/
  bootstrap/app.go
  __CONTEXT_NAME__/
    domain/__MODEL_NAME__/
    usecase/
      command/
      query/
    ports/
      http/
      module/
    adapters/postgres/
Dockerfile
.dockerignore
compose.yaml
Makefile
go.mod
README.md
```

- `domain/<model>` — связная модель, бизнес-правила и контракт репозитория агрегата.
- `usecase/command` и `query` — изменение состояния и чтение; один файл на сценарий.
- `ports` — входы, транспортные контракты и преобразование ошибок.
- `adapters` — БД, внешние клиенты и преобразование моделей хранения.
- Интерфейсы зависимостей лежат рядом с потребителем; реализации — в адаптерах.
- `domain` не зависит от внешних слоёв; `usecase` не импортирует `ports` и `adapters`.
- Между контекстами — адаптер потребителя и `ports/module` поставщика; модели и таблицы остаются внутри своего контекста.
- `bootstrap` читает конфигурацию и связывает компоненты конструкторами.

По мере появления кода: общий технический код — `internal/platform/<purpose>`,
миграции — `adapters/postgres/migrations`, тесты — рядом с кодом, сквозные —
в корневом `tests/`, конфиги инфраструктуры — в `deploy/<service>`.

```sh
make build        # бинарник в bin/
make run          # запуск
make fmt          # форматирование
make check        # форматирование, go vet, тесты
make docker-build # Docker-образ
make up           # Compose
make down
```
