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
    file_size: int | None = None


class TelegramMessage(BaseModel):
    message_id: int
    date: int
    chat: TelegramChat

    from_user: TelegramUser = Field(..., alias="from")
    photo: list[TelegramPhotoSize] | None = None
    text: str | None = None


class TelegramUpdate(BaseModel):
    update_id: int

    message: TelegramMessage | None = None
