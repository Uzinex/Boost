"""
Uzinex Boost — Utilities Package
================================

Пакет служебных инструментов (utils) для backend-системы Uzinex Boost v2.0.

Назначение:
-----------
Содержит набор универсальных вспомогательных модулей, не относящихся
к конкретным доменным областям, но используемых повсеместно в проекте.

Основные направления:
---------------------
• 🔐 crypto.py         — хэширование, JWT, подписи токенов, защита данных.  
• 🧩 validators.py     — общие проверки и валидация полей.  
• ⏰ time_utils.py     — работа с временными зонами и датами.  
• ✉️ email_utils.py    — отправка писем и шаблоны уведомлений.  
• 🧾 formatters.py     — форматирование чисел, сумм и дат.  
• 🧱 id_generator.py   — генерация уникальных кодов и UUID.  
• 📄 pagination.py     — расчёт и форматирование страниц выдачи.  
• ⚙️ exceptions.py     — базовые исключения и системные ошибки.  
• 🧠 logger.py         — расширенные настройки логирования.

Принципы:
----------
1. Универсальность — код, независимый от конкретных модулей.
2. Переиспользуемость — функции можно вызывать из любого слоя.
3. Безопасность — минимизация сторонних зависимостей.
4. Единый стиль — документация и сигнатуры в одном формате.

Пример использования:
---------------------
from utils import hash_password, validate_email, utc_now

password_hash = hash_password("secret")
is_valid = validate_email("info@uzinex.uz")
now = utc_now()
"""

from utils.crypto import hash_password, verify_password, create_jwt, decode_jwt
from utils.validators import validate_email, validate_username, validate_amount
from utils.time_utils import utc_now, to_local_time, format_timedelta
from utils.id_generator import generate_uuid, generate_ref_code

__all__ = [
    # Crypto
    "hash_password",
    "verify_password",
    "create_jwt",
    "decode_jwt",

    # Validators
    "validate_email",
    "validate_username",
    "validate_amount",

    # Time
    "utc_now",
    "to_local_time",
    "format_timedelta",

    # ID Generators
    "generate_uuid",
    "generate_ref_code",
]
