# Проверка GitHub Actions и защиты ветки

Проверено 24 ноября 2026 года.

- Репозиторий: https://github.com/ArrrinaY/sirius-food-lab10
- Зелёный CI main: https://github.com/ArrrinaY/sirius-food-lab10/actions/runs/45386244795
- Демонстрационный PR: https://github.com/ArrrinaY/sirius-food-lab10/pull/1
- Красный CI PR: https://github.com/ArrrinaY/sirius-food-lab10/actions/runs/45386605801

На main проверка tests прошла: 65 unit-тестов и 9 интеграционных.
В PR добавлен отдельный test_ci_red_demo.py с намеренным assert 1 == 2.
Он не находится в основной версии проекта.

GitHub подтвердил для PR состояние mergeStateStatus=BLOCKED,
обязательная проверка tests завершилась с conclusion=FAILURE.
Защита main требует tests и распространяется на администратора
(enforce_admins=true). Попытку реального слияния не выполняли.

Для защиты откройте зелёный запуск main, затем PR № 1 и его блок Tests:
покажите намеренную ошибку и запрет слияния. Не сливайте этот демонстрационный PR.

Репозиторий создан из текущего рабочего дерева 24 ноября 2026 года:
коммит 5d085c8 содержит ЛР 6–10, тесты, нагрузку и фикс psutil.
Старый remote SuperSlayQueen/sirius-food удалён; origin указывает
на новый репозиторий. Word-файлы и временные логи в текущем дереве отсутствуют.
