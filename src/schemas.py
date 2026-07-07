from typing import List

from pydantic import BaseModel, Field

# ==========================================
# Modelos para Telegram
# ==========================================


class TelegramChat(BaseModel):
    id: int


class TelegramUser(BaseModel):
    id: str
    is_bot: bool
    first_name: str


class TelegramPhotoSize(BaseModel):
    file_id: str
    file_unique_id: str


class TelegramMessage(BaseModel):
    chat: TelegramChat
    from_user: TelegramUser = Field(..., alias="from")
    photo: List[TelegramPhotoSize] = []


class TelegramUpdate(BaseModel):
    """Representa el payload crudo que envía el webhook de Telegram"""

    update_id: int
    message: TelegramMessage


# ==========================================
# MODELO AGNÓSTICO DE TU NEGOCIO
# ==========================================


class TransaccionPendiente(BaseModel):
    """
    El modelo ideal de tu aplicación. Cualquier plataforma (Telegram, Web, App)
    deberá convertirse a este formato antes de procesar el gasto.
    """

    usuario_id: str
    chat_id: int
    archivo_id: str
