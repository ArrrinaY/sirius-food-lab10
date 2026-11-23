# Практическая работа № 10 — запуск после распаковки ZIP и настройка CI

Инструкция для Windows и PowerShell. У каждого студента должен быть свой аккаунт GitHub и свой репозиторий. Уровень работы — 8 баллов: интеграционные тесты, нагрузка, GitHub Actions и блокировка слияния при падающих тестах.

## 1. Установить программы

- Python 3.11 или 3.12. При установке отметить **Add Python to PATH**.
- Docker Desktop. Запустить его и дождаться готовности; использовать режим Linux containers.
- Git.
- GitHub CLI — команда `gh`.

После установки открыть новый PowerShell и проверить:

```powershell
py --version
docker --version
git --version
gh --version
docker info
```

Последняя команда должна показать сведения о сервере Docker. Для первой установки зависимостей и загрузки образов нужен интернет.

## 2. Открыть корень проекта

Распаковать ZIP. Открыть PowerShell в папке, где находятся `app`, `scripts`, `tests`, `requirements-dev.txt` и `alembic.ini`.

Проверить:

```powershell
Get-Location
Test-Path requirements-dev.txt
Test-Path .github/workflows/test.yml
```

Обе проверки файлов должны вывести `True`. Если выводится `False`, перейти внутрь папки проекта, а не оставаться во внешней папке ZIP.

## 3. Создать виртуальное окружение

Для Python 3.11:

```powershell
py -3.11 -m venv .venv
```

Если установлен Python 3.12, выполнить вместо предыдущей команды:

```powershell
py -3.12 -m venv .venv
```

Затем:

```powershell
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -r requirements-dev.txt
```

Дождаться завершения установки без ошибок. Активировать окружение не требуется. В каждом новом окне PowerShell заново задавать `$py` из корня проекта:

```powershell
$py = ".\.venv\Scripts\python.exe"
```

## 4. Запустить интеграционные тесты

Docker Desktop должен работать.

```powershell
& $py -m pytest tests/integration -v
```

Ожидаемый результат: **9 passed**.

Тесты сами поднимают временные PostgreSQL 15 и Redis 7, применяют миграции Alembic и запускают отдельный API. Между тестами данные очищаются. После завершения временные контейнеры удаляются. Первый запуск может быть дольше из-за загрузки образов.

Для этой команды не требуется создавать `.env`, запускать Docker Compose или вручную поднимать API.

Что показать в коде:

- `scripts/lab10_environment.py` — Testcontainers, миграции и запуск API на случайном порту.
- `tests/integration/conftest.py` — фикстуры и очистка данных между тестами.
- `tests/integration/test_orders.py` — HTTP-проверки заказа, баланса, оплаты, авторизации, меню и Outbox.

Unit-тесты отдельно:

```powershell
& $py -m pytest -q tests/test_architecture.py tests/test_auth_service.py tests/test_grpc_client.py tests/test_orders_service.py tests/test_rate_limit.py tests/test_tasks.py tests/test_users_service.py
```

Ожидается **65 passed**. Старые тесты `test_security_api.py` и `test_menu_cache.py` относятся к прошлым работам и требуют отдельной инфраструктуры; для нового стенда используйте указанные команды.

## 5. Запустить Locust с интерфейсом

```powershell
& $py -m scripts.run_lab10_load --web
```

Дождаться строки с адресом Locust. Открыть http://127.0.0.1:8089.

Установить:

```text
Number of users: 50
Spawn rate: 10
```

Адрес временного API стенд передаёт автоматически. Запустить нагрузку, посмотреть Statistics и Charts: RPS, p95 и количество ошибок. Затем увеличить нагрузку до 200 пользователей.

У виртуальных пользователей разные аккаунты и JWT. Нагрузка выполняется на временной базе, рабочие данные проекта не используются. JWT действуют 15 минут; для нового длительного показа перезапустите стенд.

Чтобы остановить стенд, нажать **Ctrl+C в терминале**.

## 6. Получить отчёты нагрузки

После остановки интерфейсного режима выполнить:

```powershell
& $py -m scripts.run_lab10_load
```

Будут выполнены прогоны на 50 и 200 пользователей. Результаты сохраняются в `docs/lab10/load`: CSV, JSON с наблюдениями ресурсов и локальные HTML-отчёты.

Стресс-прогон с короткими паузами:

```powershell
& $py -m scripts.run_lab10_load --stress --users 200 --output docs/lab10/load/stress
```

Сравнение с двумя процессами API:

```powershell
& $py -m scripts.run_lab10_load --stress --users 200 --workers 2 --output docs/lab10/load/two_workers
```

Запускать команды по очереди. Каждая создаёт свой временный стенд. Обычный сценарий использует паузы 1–3 секунды, стресс — 0,01–0,05 секунды. Время разгона входит в длительность прогона.

Сохранённый пример анализа находится в `docs/lab10/load_results.md`. На другом компьютере результаты будут отличаться: после своего прогона нужно сравнить свои CSV и описать собственные наблюдения.

## 7. Авторизоваться в GitHub CLI

```powershell
gh auth login --hostname github.com --git-protocol https --web --scopes workflow
```

Терминал покажет одноразовый код и ссылку. Открыть предложенную ссылку, войти в свой аккаунт GitHub, ввести код из своего терминала и подтвердить доступ GitHub CLI. Дождаться сообщения об успешной авторизации.

Проверить:

```powershell
gh auth status
```

Разрешение `workflow` требуется для загрузки `.github/workflows/test.yml`. Если GitHub пишет, что workflow scope отсутствует:

```powershell
gh auth refresh --hostname github.com --scopes workflow
```

Подтвердить новый код в браузере, затем повторить отправку кода проекта.

## 8. Создать локальный Git-репозиторий

Эти команды рассчитаны на обычный ZIP без папки `.git`. Проверить:

```powershell
Test-Path .git
```

Если результат `True`, используется папка с существующей историей Git. Для этой инструкции удобнее распаковать свежий ZIP с GitHub в новую папку.

В корне свежего ZIP:

```powershell
git init -b main
```

Указать свои данные автора коммитов, заменив примеры:

```powershell
git config user.name "Имя Фамилия"
git config user.email "ВАША_ПОЧТА"
```

Добавить исходники и настройки:

```powershell
git add .gitignore .env.example README.md alembic.ini docker-compose.yml requirements.txt requirements-dev.txt locustfile.py
git add app alembic proto scripts tests loadtests observability .github sirius-food-frontend
git add delivery_server.py delivery_worker.py delivery_pb2.py delivery_pb2_grpc.py
git add -- 'docs/*.md' docs/lab10
git status --short
```

В списке не должно быть `.env`, `.venv`, `node_modules`, `.next` и временных JWT. Word-файлы заданий добавлять не требуется. Демонстрационные аккаунты и учебные пароли в исходниках и инструкциях станут публичными вместе с проектом.

Создать коммит:

```powershell
git commit -m "Практическая работа 10: интеграционные тесты, нагрузка и CI"
```

## 9. Создать свой GitHub-репозиторий

Команда создаёт публичный репозиторий в аккаунте из `gh auth status`. Публичность нужна для бесплатного использования защиты ветки в GitHub Free. Для приватного репозитория доступность защиты зависит от тарифа.

```powershell
gh repo create sirius-food-lab10 --public --source=. --remote=origin --push
```

Если имя уже занято, выбрать другое, например `sirius-food-testing`.

Открыть репозиторий:

```powershell
gh repo view --web
```

## 10. Дождаться зелёного CI

На странице своего репозитория открыть **Actions → Tests → последний запуск**.

Workflow уже находится в `.github/workflows/test.yml`. Он запускается на каждый push и pull_request, устанавливает зависимости, выполняет 65 unit-тестов и 9 интеграционных тестов, сохраняет XML-результаты.

В терминале:

```powershell
gh run list
```

Дождаться зелёной галочки. Если тесты падают, открыть упавший шаг и исправить конкретную ошибку до настройки обязательной проверки.

## 11. Настроить блокировку слияния при красном CI

Сам workflow не запрещает слияние. В своём репозитории:

1. Открыть **Settings → Branches**.
2. Нажать **Add classic branch protection rule**.
3. В **Branch name pattern** указать `main`.
4. Включить **Require status checks to pass before merging**.
5. Найти и добавить проверку **tests**.
6. Включить **Require branches to be up to date before merging**.
7. Включить **Do not allow bypassing the above settings**, чтобы владелец репозитория тоже не обходил правило.
8. Сохранить правило.

Если проверка `tests` не появляется, сначала дождаться первого завершённого запуска Actions, затем обновить страницу настроек.

## 12. Создать отдельный PR с намеренно падающим тестом

Из корня проекта:

```powershell
git switch -c codex/ci-red-demo
```

Создать демонстрационный тест:

```powershell
@'
def test_ci_blocks_broken_change():
    assert 1 == 2
'@ | Set-Content -Encoding UTF8 tests/integration/test_ci_red_demo.py
```

Сохранить и отправить ветку:

```powershell
git add tests/integration/test_ci_red_demo.py
git commit -m "Демонстрация красного CI"
git push -u origin codex/ci-red-demo
```

Создать Pull Request:

```powershell
gh pr create --base main --head codex/ci-red-demo --title "Демонстрация блокировки при красном CI" --body "Намеренно падающий тест для защиты практической работы 10. Не сливать."
gh pr view --web
```

Дождаться завершения проверки. Показать:

- ошибку на `assert 1 == 2`;
- красную обязательную проверку `tests`;
- блокировку слияния PR.

**Этот PR не сливать.** Рабочая ветка `main` остаётся зелёной.

После демонстрации вернуться к рабочему коду:

```powershell
git switch main
```

Ветка `codex/ci-red-demo` создаётся один раз. Для повторного показа достаточно открыть существующий PR; повторно создавать ветку и файл не нужно.

## 13. Порядок защиты преподавателю

1. Запустить `pytest tests/integration -v`, показать **9 passed**.
2. Объяснить создание временных контейнеров, миграции и очистку между тестами.
3. Показать в тестах проверку заказа, суммы и баланса в настоящей БД.
4. Запустить Locust, показать RPS, p95 и ошибки при 50–200 пользователях.
5. Показать свои отчёты и объяснить найденное узкое место.
6. Открыть свой зелёный запуск GitHub Actions.
7. Открыть свой PR с падающим тестом и заблокированным слиянием.

Краткие ответы:

- Unit-тест проверяет отдельную логику без внешних служб; интеграционный — взаимодействие настоящих компонентов.
- Testcontainers даёт чистую воспроизводимую среду вместо общей базы с чужими данными.
- p95: 95% запросов завершились не дольше указанного времени.
- CI запускает тесты автоматически. Обязательная проверка ветки не позволяет слить изменение с падающими тестами.
- Покрытие само по себе не доказывает качество: тест должен проверять результат, а не только выполнять строки.

## Типичные проблемы

| Проблема | Что сделать |
|---|---|
| `py` не найден | Установить Python с Add Python to PATH и открыть новый терминал |
| Docker недоступен | Запустить Docker Desktop, дождаться готовности и повторить `docker info` |
| `requirements-dev.txt` не найден | Перейти в корень проекта |
| `$py` не работает в новом окне | Повторить `$py = ".\.venv\Scripts\python.exe"` |
| Locust начал отвечать 401 после долгого сеанса | Перезапустить нагрузочный стенд для новых JWT |
| GitHub отклоняет workflow | Выполнить `gh auth refresh --hostname github.com --scopes workflow`, подтвердить доступ и повторить `git push` |
| Нет проверки `tests` в настройках ветки | Дождаться первого запуска Actions и обновить настройки |
| После создания красного теста локальные тесты падают | Вернуться на `main`: `git switch main` |

## Официальная документация

- Публикация локального проекта: https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github?platform=windows
- Защита ветки: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule
