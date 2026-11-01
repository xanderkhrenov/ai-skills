## Сетевые контракты

Источник правды — `proto/__PROJECT_NAME__/<context>/v1/*.proto`, protobuf package
`__API_NAMESPACE__.<context>.v1`. HTTP-маршруты и OpenAPI tags по контекстам задаются
в `.proto`. `openapi/__PROJECT_NAME__.yaml` — сгенерированный OpenAPI 2.0.
Внутренние Go-интерфейсы контекстов сюда не переносятся.

Настройки и версии генераторов — `buf.gen.yaml`, `toolchain.json`, npm lockfile.
Зависимости protobuf закреплены в `buf.lock`. После намеренного изменения
protobuf-зависимостей обнови его через `buf dep update`.

Из основного репозитория: `make generate`, `make generate-check`, `make contract-check`.
Коммить `.proto`, настройки и производный OpenAPI вместе, затем результаты
генерации в backend и UI и обновлённые ссылки на подмодули в основном репозитории.
Обычные сборки используют уже закоммиченный код.
