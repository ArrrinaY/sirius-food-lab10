# Проверка GitHub Actions и защиты ветки

Проверено 23 ноября 2026 года.

- Репозиторий: https://github.com/SuperSlayQueen/sirius-food
- Зелёный CI main: https://github.com/SuperSlayQueen/sirius-food/actions/runs/45246496223
- Демонстрационный PR: https://github.com/SuperSlayQueen/sirius-food/pull/1
- Красный CI PR: https://github.com/SuperSlayQueen/sirius-food/actions/runs/45246723152

На main проверка tests прошла: 65 unit-тестов и 9 интеграционных.
В PR добавлен отдельный test_ci_red_demo.py с намеренным assert 1 == 2.
Он не находится в основной версии проекта.

GitHub подтвердил для PR состояние mergeStateStatus=BLOCKED,
обязательная проверка tests завершилась с conclusion=FAILURE.
Защита main требует tests и распространяется на администратора
(enforce_admins=true). Попытку реального слияния не выполняли.

Для защиты откройте зелёный запуск main, затем PR № 1 и его блок Tests:
покажите намеренную ошибку и запрет слияния. Не сливайте этот демонстрационный PR.

Публичная версия опубликована из отдельного снимка рабочей папки
(локальная ветка codex/lab10-public, каталог .pytest_cache/lab10-publish),
чтобы не публиковать старые Word-документы из истории Git.
Исходная локальная история main сохранена. Для дальнейшей работы
с опубликованным репозиторием удобно сделать новый клон в отдельную папку;
не выполняйте принудительную отправку старой локальной main поверх GitHub.
