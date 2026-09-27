# Разработка и локальный запуск

## Состояние реализации

Реализован backend MVP: регистрация и JWT, ротация refresh-сессий с защитой от replay, профиль, workspace, участники и RBAC, проекты, теги, задачи, фильтры и пагинация. Добавлены две миграции, Redis rate limiting, health-маршруты, JSON-логи и метрики Prometheus. Адаптивный frontend по `prototype/template.png` подключён к API; его запуск и устройство описаны в [FRONTEND.md](FRONTEND.md).

Краткое описание проекта и быстрый запуск находятся в корневом [README.md](../README.md). Локальная спецификация находится в игнорируемой папке `rules/`.

## Python и PowerShell

Нужны Python 3.12+ и Docker Compose. На текущем компьютере `.venv` уже создана. Для разрешения локального Activate.ps1 только в текущем окне PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

На новом компьютере:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install uv
.\.venv\Scripts\uv.exe sync --frozen
.\.venv\Scripts\python.exe scripts/bootstrap_env.py
```

`bootstrap_env.py` создаёт `.env` из примера и генерирует JWT-секрет. Непустой существующий `.env` сохраняется. Содержимое `.env` не публикуется. Lock-файл закрепляет версии Python-пакетов для Windows и Linux.

## Запуск через Docker

```powershell
docker compose up -d --build --wait
```

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Liveness: http://127.0.0.1:8000/health/live
- Readiness: http://127.0.0.1:8000/health/ready
- Метрики: http://127.0.0.1:8000/metrics
- PostgreSQL: `127.0.0.1:5433`; Redis: `127.0.0.1:6380`.

Миграции выполняет одноразовый сервис `migrations` до старта API. PgAdmin включается отдельно командой `docker compose --profile tools up -d pgadmin` и доступен на http://127.0.0.1:5050. Его локальные настройки указаны в Compose; профиль инструментов не нужен для работы API.

Порты публикуются только на loopback. Для production требуются TLS, приватный доступ к PostgreSQL/Redis/метрикам, собственные секреты и backup-политика. Пример Compose является локальным окружением, а не готовым production-развёртыванием. Uvicorn по умолчанию не доверяет forwarded headers; при использовании reverse proxy явно настройте доверенные адреса, иначе rate limit будет учитывать адрес прокси.

Если Docker отсутствует в PATH на текущем компьютере, его исполняемый файл находится в `%LOCALAPPDATA%\Programs\DockerDesktop\resources\bin\docker.exe`.

## Запуск API из .venv

```powershell
docker compose up -d postgres redis
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:create_app --factory --reload --port 8000 --no-access-log --no-proxy-headers
```

API из Docker и локальный Uvicorn не должны одновременно занимать порт 8000. Для диагностики используйте `request_id` в ответе и логах. Секреты, HTTP-тела, токены и значения SQL-параметров не записываются в логи.

## Тесты и проверки

В PowerShell весь обязательный цикл можно выполнить командой `./scripts/check.ps1`. Скрипт останавливается на первой ошибке. `./scripts/check.ps1 -UnitOnly` запускает быстрые проверки без Docker и не заменяет полную приёмку.

```powershell
docker compose -f compose.test.yaml up -d --wait postgres redis
$env:RUN_INTEGRATION = '1'
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\black.exe --check .
.\.venv\Scripts\mypy.exe app tests scripts
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing --cov-report=xml
```

Тестовая PostgreSQL использует порт 55432 и БД `taskman_test`, Redis — порт 56379 и БД 15. Интеграционные тесты очищают только это выделенное окружение. В нём нельзя хранить пользовательские данные. Без `RUN_INTEGRATION=1` интеграционные проверки пропускаются; такой запуск не является полной приёмкой.

Для покрытия Python 3.12 используется `coverage` с `sys.monitoring`: это позволяет корректно учитывать async-сценарии SQLAlchemy с greenlet. Порог покрытия строк — 80%. Отдельный отчёт по ветвлениям:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-branch --cov-fail-under=0 --cov-report=xml:coverage-branches.xml
```

На Python 3.12 coverage может переключить этот прогон на другой tracer, так как поддержка ветвлений в sys.monitoring зависит от версии Python. Порог строк при этом не отключается в основном прогоне. CI повторяет линтинг, форматирование, типизацию, интеграционные тесты и оба отчёта.

## Поведение API

Используйте `POST /api/v1/auth/register`, затем `/auth/login` и передавайте access-токен в `Authorization: Bearer …`. Refresh-токен передаётся в JSON-теле. Хранятся только хеши refresh-токенов. Клиент должен обновлять токен последовательно; конкурентное или повторное обновление отзывает семью сессии. Access-токен продолжает действовать до своего короткого срока истечения.

Списки возвращают `items`, `total`, `limit`, `offset`. Фильтры задач: `project_id`, повторяемые `statuses`, `priorities`, `tag_ids`, `assignee_id`, `created_by`, `unassigned`, `due_from`, `due_to`, `overdue`, `q`, `sort`, `direction`. Несколько тегов означают наличие всех тегов. Пример: `/api/v1/workspaces/{id}/tasks?statuses=todo&statuses=in_progress&sort=priority&direction=desc`.

В PATCH отсутствие поля сохраняет его значение; `null` обнуляет только `due_at`, `assignee_id`, `color`. Роли актуальны на момент транзакции. Записи одного workspace берут общую блокировку workspace перед проверкой прав; это обеспечивает корректность гонок ролей и назначений, но ограничивает параллельные записи внутри одного workspace. Переход к более мелким блокировкам требует отдельного нагрузочного исследования.

Rate limit использует атомарное фиксированное окно Redis, отсчитываемое от первого запроса. Значения по умолчанию соответствуют спецификации; переопределяются переменными `RATE_LOGIN_PER_IP`, `RATE_LOGIN_PER_ACCOUNT`, `RATE_REGISTER_PER_IP`, `RATE_REFRESH_PER_IP`, `RATE_AUTHENTICATED`, `RATE_ANONYMOUS`. Ответ `429` содержит `Retry-After`; недоступный Redis даёт `503`. Health-маршруты не ограничиваются. IP и email в ключах Redis заменены HMAC.

## Миграции и нагрузочная проверка

`alembic check` сравнивает ORM со схемой. Первая миграция создаёт таблицы и справочник ролей, вторая добавляет `pg_trgm` и GIN-индексы. Не редактируйте уже применённые миграции при дальнейшей разработке.

Нагрузочный сценарий работает исключительно с тестовым Compose и очищает его данные. Не запускайте параллельно с integration-тестами:

```powershell
docker compose -f compose.test.yaml --profile benchmark up -d --wait
.\.venv\Scripts\python.exe scripts/benchmark.py --duration 600 --rate 50
```

Предварительно должен быть собран образ `task-management-api:0.1.0`. Сценарий создаёт 100 workspace, 1 000 проектов и 100 000 задач; выполняет 80% чтений и 20% обновлений через настоящий HTTP. API ограничен 2 CPU / 2 GiB, PostgreSQL — 2 CPU / 4 GiB. Результат сохраняется в `docs/benchmark.json`. Auth-хеширование не входит в этот профиль; работа на Docker Desktop не гарантирует тех же результатов в production.

## Ограничения текущей версии

Отсутствуют billing, восстановление пароля, подтверждение email, уведомления, файлы, фоновые задачи и приватные проекты — они не входят в согласованный backend MVP. Сессия frontend хранится в памяти страницы и требует повторного входа после reload. Метрики хранятся в памяти процесса; при нескольких репликах их собирают отдельно и агрегируют снаружи. Production RPO/RTO требуют проверки в выбранном окружении хранения резервных копий.

Использованные первичные справочники: [SQLAlchemy AsyncIO](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html), [FastAPI async tests](https://fastapi.tiangolo.com/advanced/async-tests/), [uv projects](https://docs.astral.sh/uv/guides/projects/).

## Web-интерфейс

Рабочий frontend добавлен в `frontend/`. Docker-версия открывается на
<http://127.0.0.1:3000>; Vite для разработки — на <http://127.0.0.1:5173>.
Команды запуска, архитектура и ограничения сессии: [FRONTEND.md](FRONTEND.md).
