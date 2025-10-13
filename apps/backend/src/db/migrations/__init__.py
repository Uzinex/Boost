"""
Uzinex Boost — Database Migrations Package
===========================================

Пакет миграций Alembic для управления схемой PostgreSQL базы данных Boost v2.0.

Назначение:
- централизованное хранение миграций (`versions/`);
- интеграция с SQLAlchemy metadata (`core.database.Base`);
- связь с Alembic через `env.py` и `alembic.ini`.

Используется командами:
    alembic revision --autogenerate -m "message"
    alembic upgrade head
    alembic downgrade -1
"""

__all__ = ["__version__", "__author__"]

__version__ = "2.0.0"
__author__ = "Uzinex Engineering Team"
