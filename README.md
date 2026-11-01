# ai-skills

Коллекция навыков для AI-агентов. Лицензия [MIT](LICENSE).

## Навыки

- [go-backend-template](skills/go-backend-template) — Go-монолит с DDD и Clean Architecture; опциональный профиль с отдельными UI/IDL-подмодулями и protobuf-first API.

## Установка в Codex

В чате Codex выполни:

```text
$skill-installer Установи https://github.com/xanderkhrenov/ai-skills/tree/master/skills/go-backend-template
```

После установки навык доступен со следующего сообщения.

## Использование

```text
$go-backend-template Создай проект orders-service в ./orders-service
```

Для генерации нужны Python 3 и Go; для соответствующих команд — Make и Docker.
Для обычного backend директория должна быть новой или пустой.
Профиль `fullstack` дополняет существующий репозиторий с инициализированными
подмодулями `ui` и `idl`: React/TypeScript/Vite, gRPC-Gateway, Buf и генерация
Fetch-клиента. Для генерации также нужны Buf, Node/npm; версии закреплены в профиле.

```text
$go-backend-template Подготовь fullstack-каркас в существующем проекте с подмодулями ui и idl
```
