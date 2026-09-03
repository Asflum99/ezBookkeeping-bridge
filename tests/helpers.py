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
    "cuentas": {"BCP": "3826102909318201345"},
    "cuentas_hints": [("BCP", "Yape, BCP Transfer, morado, 4821", 2)],
    "categorias": {"Comida": "3826101146502561820"},
}

TRANSFER_USER_INFO = {
    "nombre": "Test User",
    "ez_token": "fake-jwt-token",
    "cuentas": {
        "billetera_digital": "3826102909318201344",
        "tarjeta_ripley": "3826102909318201345",
    },
    "cuentas_hints": [
        ("billetera_digital", "Yape, BCP Transfer, morado", 2),
        ("tarjeta_ripley", "Ripley, 4821, tarjeta", 3),
    ],
    "categorias": {
        "Comida": "3826101146502561820",
        "Transferencia Bancaria": "3826101146502561821",
        "Pago de Tarjetas de Crédito": "3826101146502561822",
    },
}

SANITIZED_DATA = {
    "amount": 25.50,
    "date_time": "2026-07-19 12:30:00",
    "payment_account": "billetera_digital",
    "category": "Comida",
    "comment": "Tambo",
}

TRANSFER_SANITIZED_DATA = {
    "amount": 100.00,
    "date_time": "2026-07-19 12:30:00",
    "payment_account": "billetera_digital",
    "category": None,
    "comment": "Pago tarjeta",
    "transaction_type": 4,
    "category_id": "3826101146502561822",
    "destination_account_id": "3826102909318201345",
    "destination_account_category": 3,
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
