## Frontend

React + TypeScript + Vite; npm и `package-lock.json`. После `npm ci`:
`npm run dev`, `npm run check`, `npm run build` (артефакт `dist/`).

`src/api/generated` — генерируемый Fetch-клиент; модули группируются по первому
OpenAPI tag контекста. Генерация запускается из основного репозитория через
`make generate`. Файлы клиента коммитятся; сборке UI не нужны Go или Buf.

В разработке `/api/` проксируется на `http://127.0.0.1:8080`; адрес переопределяется
через `API_PROXY_TARGET`. В production Dockerfile собирает отдельный frontend;
его HTTP-сервер раздаёт статику и проксирует `/api/` в сервис `backend`.
Для другого окружения настрой reverse proxy в `nginx.conf`.
