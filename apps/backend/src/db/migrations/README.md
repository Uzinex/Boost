# 🗄️ Uzinex Boost — Database Migrations (Alembic)

## 📘 Обзор

Папка **`apps/backend/src/db/migrations/`** содержит всю историю изменений схемы базы данных проекта **Uzinex Boost v2.0**.

Используется библиотека **[Alembic](https://alembic.sqlalchemy.org/)** — официальный инструмент миграций SQLAlchemy.

---

## ⚙️ Основные файлы

| Файл / Папка | Назначение |
|---------------|-------------|
| `env.py` | Конфигурация Alembic — подключение к БД, загрузка `Base.metadata` |
| `script.py.mako` | Шаблон для генерации новых миграций |
| `versions/` | Каталог с файлами миграций (`upgrade` / `downgrade`) |
| `README.md` | Документация по работе с миграциями |
| `__init__.py` | Делает пакет импортируемым |
| `alembic.ini` *(в корне проекта)* | Конфигурация CLI для Alembic |

---

## 🚀 Основные команды

> Все команды выполняются из корня проекта (где лежит `alembic.ini`).

### 1️⃣ Создание новой миграции

Автоматическая генерация по изменениям ORM-моделей:

```bash
alembic revision --autogenerate -m "init database"
