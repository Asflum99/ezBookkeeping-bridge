SAMPLE_PHOTO = {
    "file_id": "photo_large_id",
    "file_unique_id": "uniq_large",
    "width": 1280,
    "height": 720,
    "file_size": 1048576,
}


VALID_USER_INFO = {
    "nombre": "Test User",
    "ez_token": "fake-jwt-token",
    "cuentas": {"BCP": "3826102909318201344"},
    "cuentas_hints": [("BCP", "Yape, BCP Transfer, morado", 2)],
    "categorias": {"Comida": "3826101146502561820"},
}

SANITIZED_DATA = {
    "amount": 25.50,
    "date_time": "2026-07-19 12:30:00",
    "payment_account": "billetera_digital",
    "category": "Comida",
    "comment": "Tambo",
}

WEBHOOK_PATH = "/webhook/telegram/"


def make_text_update(**overrides):
    base = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 12345, "type": "private"},
            "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            "text": "/update-accounts",
        },
    }
    base.update(overrides)
    return base


def make_photo_update(**overrides):
    base = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 12345, "type": "private"},
            "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            "photo": [SAMPLE_PHOTO],
        },
    }
    base.update(overrides)
    return base
