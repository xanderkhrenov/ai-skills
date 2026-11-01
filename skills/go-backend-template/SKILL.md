---
name: go-backend-template
description: Scaffold a Go backend modular monolith with DDD and Clean Architecture in the ThreeDotsLabs style, using usecase instead of app, and a concise Russian README. Use for creating a new project skeleton, not implementing features or refactoring an existing application.
---

# Go Backend Template

Создавай только шаблон проекта и лаконичный README по согласованной структуре.
Используй готовые файлы из `assets/template` через `scripts/scaffold.py`.

## Параметры и запуск

Определи каталог назначения и имя проекта из запроса или текущего контекста.
Генератор принимает новый или пустой каталог и не перезаписывает файлы.
Если выбранная директория непустая, выведи только «Директория должна быть пустой.»
и остановись. Другой каталог автоматически не выбирай.

Используй указанный пользователем Go module path. Если он не указан, возьми имя
проекта как локальный module path; не придумывай GitHub-аккаунт или удалённый репозиторий.
Версию Go возьми из запроса, иначе из `go env GOVERSION`, убрав префикс `go`.
Если Go недоступен и версия неизвестна, уточни её.
По умолчанию контекст и модель называются `example`; используй предметные имена,
если пользователь их уже задал.

```sh
python3 <skill-dir>/scripts/scaffold.py <destination> \
  --name <project-name> --module <module-path> --go-version <version> \
  --context <context-name> --model <model-name>
```

## Состав и границы

- Один корневой `go.mod`, вход `cmd/<project>`, сборка в `internal/bootstrap`.
- Контекст: `internal/<context>/{domain/<model>,usecase/{command,query},ports/{http,module},adapters/postgres}`.
- В терминологии ThreeDotsLabs `ports` — входные обработчики, `adapters` — исходящие подключения.
- Контракт репозитория относится к доменной модели; остальные интерфейсы зависимостей — к сценарию-потребителю.
- Другие контексты доступны через их `ports/module` из адаптера интеграции.
- `platform`, `tests`, миграции и `deploy` описаны в README и появляются вместе с реализациями; пустые каталоги и `.gitkeep` не добавляй.
- Dockerfile, `.dockerignore`, `compose.yaml`, Makefile — в корне.

Не добавляй бизнес-логику, примеры сценариев, тесты, архитектурные проверки,
линтеры, CI, сторонние Go-зависимости или длинное руководство, если их отдельно
не запросили. Не копируй код и документацию из текущего проекта поверх шаблона.

Проверь генерацию, форматирование и сборку доступными локальными инструментами
(`make check build`, `docker compose config --quiet`). Не запускай контейнеры
и не создавай Git-репозиторий автоматически. В ответе дай ссылку на результат
и кратко укажи выполненные проверки.
