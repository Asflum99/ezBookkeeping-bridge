from typing import List, Optional

from pydantic import BaseModel, Field


class TelegramChat(BaseModel):
    id: int
    type: str


class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str


class TelegramPhotoSize(BaseModel):
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None


class TelegramMessage(BaseModel):
    message_id: int
    date: int
    chat: TelegramChat

    from_user: Optional[TelegramUser] = Field(None, alias="from")
    photo: Optional[List[TelegramPhotoSize]] = None


class TelegramUpdate(BaseModel):
    update_id: int

    message: Optional[TelegramMessage] = None


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
