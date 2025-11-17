# MeatBot Production Suite

Комплекс для управления мясоперерабатывающим цехом: Telegram‑бот автоматизирует работу смен, а Django CRM обеспечивает офисные процессы, контроль качества и хранение данных. Репозиторий демонстрирует типовой продакшен-стек с интеграцией MinIO, Redis и PostgreSQL, а также примеры тонкой настройки админки и телеграм-форм.

---

## Ключевые возможности
- Телеграм-бот на `aiogram` для каждой роли цеха: дефростер, лаборант, фасовщик, кладовщик, технолог и др.
- Состояния (`bot/states`) и формы с пошаговыми проверками, автосохранениями и inline-клавиатурами.
- Django CRM с моделями сырья, партий, рецептов, статусов, документами и продвинутой админкой (фильтры, агрегаты, MinIO storage).
- Планировщик `APScheduler` для циклических задач (контроль статусов, уведомления, проверка загруженности линий).
- Хранилище файлов в MinIO, генерация Excel/Docx отчётов, выгрузки в админке.
- Готовая Docker Compose-инфраструктура: `bot`, `django`, `postgres`, `redis`, `minio`, `pgadmin`.

---

## Архитектура

### Telegram-бот (`bot/`)
- `app.py` поднимает Django-контекст, запускает APScheduler и polling aiogram.
- `bot/handlers/*` разделены по должностям; внутри — бизнес-логика шагов, валидации, уведомления и взаимодействие с CRM через `bot.utils.api`.
- `bot/states` описывают FSM для ввода весов, статусов партий, выборов рецептов.
- `bot/keyboards` генерируют Reply/InlineMarkup, включая динамические списки из БД.
- `bot/utils` содержит API-клиенты, Excel/Docx генераторы, работу с MinIO и вспомогательные хелперы.
- `middlewares` реализуют локализацию, логирование и подгрузку пользовательских контекстов.

### Django CRM (`Web/`)
- Приложение `Web/CRM` описывает доменную модель (сырьё, партии, рецепты, статусы, загрузки шокеров и т.д.) и сигналами синхронизирует derived-данные.
- `Web/CRM/admin.py` включает расширенную админку с `rangefilter`, `admin_totals`, кастомными формами и действиями.
- `Web/CRM/views/*` и `management/commands` дают API/сервисы для бота, формируют печатные документы и сводные отчёты.
- Статика (`Web/static`) и шаблоны (`Web/templates`) переопределяют административный интерфейс.

### Общие сервисы
- `data/config.py` описывает обязательные переменные окружения и точку входа `.env`.
- MinIO используется Django-хранилищем `django_minio_backend` (безопасные бакеты, expiring URLs).
- Redis зарезервирован под FSM (`MemoryStorage` легко переключается на RedisStorage2).
- Планировщик (`scheduler` в `bot/loader.py`) выполняет задачи каждые 4 секунды для мониторинга статусов по ролям.

---

## Технологический стек

| Слой | Технологии |
| --- | --- |
| Бэкенд-бот | Python 3.10, aiogram 2.25, APScheduler, aiohttp |
| CRM | Django 4.2, PostgreSQL 14, django-admin-rangefilter, django-minio-backend |
| Интеграции | MinIO, Redis, pgAdmin, requests/openpyxl/python-docx |
| Деплой | Docker, Docker Compose, Uvicorn (для ASGI, если требуется) |

---

## Структура репозитория

- `app.py` — единая точка запуска aiogram + Django.
- `bot/handlers` — доменные сценарии для ролей цеха.
- `bot/states`, `bot/keyboards`, `bot/middlewares`, `bot/utils` — FSM, UI и инфраструктурные слои.
- `Web/web` — настройки Django, URL, WSGI/ASGI.
- `Web/CRM` — модели, админка, формы, management-команды, util-функции.
- `data/` — настройки окружения и константы.
- `docker-compose.yaml`, `Dockerfile` — инфраструктура для локального запуска.

---

## Переменные окружения

Файл `.env` (пример пути: `data/.env` через `DATA_DIR`) должен содержать:

| Переменная | Назначение |
| --- | --- |
| `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | доступ к PostgreSQL |
| `TELEGRAM_BOT_TOKEN` | токен BotFather |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` | FSM/кэш (можно оставить локальный Redis по умолчанию) |
| `MINIO_ENDPOINT`, `MINIO_USE_HTTPS`, `MINIO_MAIN_BUCKET`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | настройки MinIO |
| `ADMIN_USER`, `ADMIN_PASSWORD` | Django superuser для автосоздания |
| `HOST`, `LOGIN`, `DEVELOPER` и др. | служебные параметры CRM/интеграций |

---

## Локальный запуск

### Через Docker Compose
```bash
cp data/.env.example .env        # подготовьте переменные
docker compose up --build
```
Сервисы:
- `bot` — Telegram-бот (`python app.py`).
- `django` — панель на `http://localhost:80`.
- `db` — PostgreSQL (порты берутся из `.env`).
- `redis` — брокер/кэш.
- `minio` — объектное хранилище (`9002`, консоль `40135`).
- `pgadmin` — визуальный клиент БД (`localhost:9999`).

### Ручной запуск
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp data/.env.example data/.env   # заполните значения
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python app.py                    # старт бота + планировщика
python manage.py runserver       # в отдельном терминале для CRM
```

---

## Доменные сценарии и автоматизация
- **Приёмка сырья** (`bot/handlers/raw_meat_batch`, `Web/CRM/models.RawMeatBatch`): загрузка документов, температур, фото, запись в CRM и MinIO.
- **Дефрост, лаборатория, миксеры, пресс, упаковка**: отдельные FSM, статусы, контроль выполнения (каждые 4 секунды APScheduler проверяет незавершённые задачи и пушит уведомления).
- **Вторичный фарш и шокеры**: модели `SecondMincedMeat`, `ShockerCamera` с расчётом доступных ресурсов и блокировками.
- **Документооборот**: `bot/utils/excel.py`, `bot/utils/docx.py`, `Web/CRM/utils.py` формируют накладные, отчёты и лабораторные листы.
- **Локализация**: `LocaleManager` + `I18nMiddleware` грузят языковые файлы из `locales/`.

---

## Наблюдаемость и логи
- Логирование построено на стандартном `logging` + `loguru` (см. `bot/utils/logging`).
- Планировщик шумоподавлен в `app.py` (понижены уровни `apscheduler` и `aiogram`).
- Стандартные Django-миграции/сигналы обеспечивают консистентность данных.

---

## Тестирование и качество
- Django-проекты используют встроенный тестовый раннер: `python manage.py test`.
- Для бот-логики рекомендованы модульные тесты FSM/handlers (не включены, но структуры разделены для простого покрытия).
- Докеризированная инфраструктура позволяет легко поднимать стенды для QA/демо.

---

## Безопасность
- Секреты и токены не закоммичены; используйте `.env`.
- Отладочный режим включён по умолчанию — выключайте `DEBUG` и меняйте `SECRET_KEY` перед продакшеном.
- MinIO конфигурируется на приватные бакеты, а ссылки выдаются с TTL.

---

Используйте репозиторий как референс по построению гибридной системы «Telegram-бот + Django CRM» с общим доменом, инфраструктурой и автоматизированными производственными сценариями.
