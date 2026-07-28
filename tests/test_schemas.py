import pytest
from pydantic import ValidationError

from schemas import (
    TelegramChat,
    TelegramMessage,
    TelegramPhotoSize,
    TelegramUpdate,
    TelegramUser,
)


class TestTelegramChat:
    def test_telegram_chat_valid_data(self):
        """Verify that TelegramChat instantiates correctly with valid types."""
        data = {"id": 123456789, "type": "private"}

        chat = TelegramChat.model_validate(data)

        assert chat.id == 123456789
        assert chat.type == "private"

    def test_telegram_chat_coercion(self):
        """Verify that Pydantic properly coerces compatible types (e.g., string integer to int)."""
        data = {
            "id": "987654321",
            "type": "group",
        }

        chat = TelegramChat.model_validate(data)

        assert chat.id == 987654321
        assert isinstance(chat.id, int)

    @pytest.mark.parametrize(
        "incomplete_payload, missing_field",
        [
            ({"id": 123456789}, "type"),
            ({"type": "group"}, "id"),
        ],
        ids=["missing_type", "missing_id"],
    )
    def test_telegram_chat_missing_required_fields(
        self, incomplete_payload, missing_field
    ):
        """Verify that ValidationError is raised when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramChat.model_validate(incomplete_payload)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (missing_field,)
        assert errors[0]["type"] == "missing"

    @pytest.mark.parametrize(
        "invalid_payload, expected_field, expected_error_type",
        [
            (
                {"id": "not_an_int", "type": "private"},
                "id",
                "int_parsing",
            ),
            (
                {"id": 123456789, "type": ["not", "a", "string"]},
                "type",
                "string_type",
            ),
        ],
        ids=["invalid_id_type", "invalid_type_type"],
    )
    def test_telegram_chat_invalid_types(
        self, invalid_payload, expected_field, expected_error_type
    ):
        """Verify that ValidationError is raised when field type cannot be converted."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramChat.model_validate(invalid_payload)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (expected_field,)
        assert errors[0]["type"] == expected_error_type


class TestTelegramUser:
    def test_telegram_user_valid_data(self):
        """Verify that TelegramUser instantiates correctly with valid types."""
        data = {"id": 123456789, "is_bot": False, "first_name": "foo"}

        user = TelegramUser.model_validate(data)

        assert user.id == 123456789
        assert not user.is_bot
        assert user.first_name == "foo"

    def test_telegram_user_coercion(self):
        """Verify that Pydantic properly coerces compatible types (e.g., string integer to int)."""
        data = {"id": "987654321", "is_bot": "false", "first_name": "foo"}

        user = TelegramUser.model_validate(data)

        assert user.id == 987654321
        assert isinstance(user.id, int)
        assert not user.is_bot
        assert isinstance(user.is_bot, bool)

    @pytest.mark.parametrize(
        "incomplete_payload, missing_field",
        [
            ({"is_bot": False, "first_name": "Alice"}, "id"),
            ({"id": 123456, "first_name": "Alice"}, "is_bot"),
            ({"id": 123456, "is_bot": False}, "first_name"),
        ],
        ids=["missing_id", "missing_is_bot", "missing_first_name"],
    )
    def test_telegram_user_missing_required_fields(
        self, incomplete_payload, missing_field
    ):
        """Verify that ValidationError is raised when any required field is missing."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramUser.model_validate(incomplete_payload)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (missing_field,)
        assert errors[0]["type"] == "missing"

    @pytest.mark.parametrize(
        "invalid_payload, expected_field, expected_error_type",
        [
            (
                {"id": "not_an_int", "is_bot": False, "first_name": "Alice"},
                "id",
                "int_parsing",
            ),
            (
                {"id": 123456, "is_bot": ["not", "a", "bool"], "first_name": "Alice"},
                "is_bot",
                "bool_type",
            ),
            (
                {"id": 123456, "is_bot": False, "first_name": ["not", "a", "str"]},
                "first_name",
                "string_type",
            ),
        ],
        ids=["invalid_id_type", "invalid_is_bot_type", "invalid_first_name_type"],
    )
    def test_telegram_user_invalid_types(
        self, invalid_payload, expected_field, expected_error_type
    ):
        """Verify that ValidationError is raised when field type cannot be converted."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramUser.model_validate(invalid_payload)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (expected_field,)
        assert errors[0]["type"] == expected_error_type


class TestPhotoSize:
    def test_photo_size_valid_data(self):
        """Verify that PhotoSize instantiates correctly with all fields."""
        data = {
            "file_id": "AgACAgEAAxkBAAIBZ2X_a8123A_BcXyZ",
            "file_unique_id": "AQAD9r4xG20FAAN_",
            "width": 1280,
            "height": 720,
            "file_size": 1048576,
        }

        photo = TelegramPhotoSize.model_validate(data)

        assert photo.file_id == "AgACAgEAAxkBAAIBZ2X_a8123A_BcXyZ"
        assert photo.file_unique_id == "AQAD9r4xG20FAAN_"
        assert photo.width == 1280
        assert photo.height == 720
        assert photo.file_size == 1048576

    def test_photo_size_optional_fields(self):
        """Verify that file_size defaults to None when omitted."""
        data = {
            "file_id": "AgACAgEAAxkBAAIBZ2X_a8123A_BcXyZ",
            "file_unique_id": "AQAD9r4xG20FAAN_",
            "width": 320,
            "height": 240,
        }

        photo = TelegramPhotoSize.model_validate(data)

        assert photo.file_size is None

    @pytest.mark.parametrize(
        "incomplete_payload, missing_field",
        [
            (
                {"file_unique_id": "AQAD_", "width": 100, "height": 100},
                "file_id",
            ),
            (
                {"file_id": "AgAC_", "width": 100, "height": 100},
                "file_unique_id",
            ),
            (
                {"file_id": "AgAC_", "file_unique_id": "AQAD_", "height": 100},
                "width",
            ),
            (
                {"file_id": "AgAC_", "file_unique_id": "AQAD_", "width": 100},
                "height",
            ),
        ],
        ids=[
            "missing_file_id",
            "missing_file_unique_id",
            "missing_width",
            "missing_height",
        ],
    )
    def test_photo_size_missing_required_fields(
        self, incomplete_payload, missing_field
    ):
        """Verify that ValidationError is raised when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramPhotoSize.model_validate(incomplete_payload)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (missing_field,)
        assert errors[0]["type"] == "missing"


class TestTelegramMessage:
    def test_telegram_message_valid_data(self):
        """Verify that TelegramMessage instantiates correctly with nested objects and optional photo list."""
        data = {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 100200300, "type": "private"},
            "from": {
                "id": 987654,
                "is_bot": False,
                "first_name": "Bob",
            },
            "photo": [
                {
                    "file_id": "photo_small_id",
                    "file_unique_id": "uniq_small",
                    "width": 320,
                    "height": 240,
                },
                {
                    "file_id": "photo_large_id",
                    "file_unique_id": "uniq_large",
                    "width": 1280,
                    "height": 720,
                },
            ],
        }

        msg = TelegramMessage.model_validate(data)

        assert msg.message_id == 1
        assert msg.date == 1700000000

        assert isinstance(msg.chat, TelegramChat)
        assert msg.chat.id == 100200300
        assert msg.chat.type == "private"

        assert isinstance(msg.from_user, TelegramUser)
        assert msg.from_user.id == 987654
        assert msg.from_user.first_name == "Bob"

        assert msg.photo is not None
        assert len(msg.photo) == 2
        assert isinstance(msg.photo[0], TelegramPhotoSize)
        assert msg.photo[0].file_id == "photo_small_id"

    def test_telegram_message_optional_photo_defaults_to_none(self):
        """Verify that photo defaults to None when omitted in text-only messages."""
        data = {
            "message_id": 2,
            "date": 1700000000,
            "chat": {"id": 100200300, "type": "group"},
            "from": {"id": 987654, "is_bot": False, "first_name": "Bob"},
        }

        msg = TelegramMessage.model_validate(data)

        assert msg.photo is None

    def test_telegram_message_with_text(self):
        """Verify that text field is parsed correctly."""
        data = {
            "message_id": 3,
            "date": 1700000000,
            "chat": {"id": 100200300, "type": "private"},
            "from": {"id": 987654, "is_bot": False, "first_name": "Bob"},
            "text": "/add_account billetera_digital 123456",
        }

        msg = TelegramMessage.model_validate(data)

        assert msg.text == "/add_account billetera_digital 123456"
        assert msg.photo is None

    def test_telegram_message_optional_text_defaults_to_none(self):
        """Verify that text defaults to None when omitted in photo messages."""
        data = {
            "message_id": 4,
            "date": 1700000000,
            "chat": {"id": 100200300, "type": "private"},
            "from": {"id": 987654, "is_bot": False, "first_name": "Bob"},
            "photo": [
                {
                    "file_id": "photo_id",
                    "file_unique_id": "uniq_id",
                    "width": 320,
                    "height": 240,
                }
            ],
        }

        msg = TelegramMessage.model_validate(data)

        assert msg.text is None
        assert msg.photo is not None

    @pytest.mark.parametrize(
        "incomplete_payload, missing_field",
        [
            (
                {
                    "date": 1700000000,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "A"},
                },
                "message_id",
            ),
            (
                {
                    "message_id": 1,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "A"},
                },
                "date",
            ),
            (
                {
                    "message_id": 1,
                    "date": 1700000000,
                    "from": {"id": 1, "is_bot": False, "first_name": "A"},
                },
                "chat",
            ),
            (
                {
                    "message_id": 1,
                    "date": 1700000000,
                    "chat": {"id": 1, "type": "private"},
                },
                "from",
            ),
        ],
        ids=["missing_message_id", "missing_date", "missing_chat", "missing_from"],
    )
    def test_telegram_message_missing_required_fields(
        self, incomplete_payload, missing_field
    ):
        """Verify that ValidationError is raised when required root fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            TelegramMessage.model_validate(incomplete_payload)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == (missing_field,)
        assert errors[0]["type"] == "missing"

    def test_telegram_message_invalid_nested_data(self):
        """Verify that validation errors bubble up from nested models with proper location tuple."""
        data = {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 100200300},
            "from": {"id": 987654, "is_bot": False, "first_name": "Bob"},
        }

        with pytest.raises(ValidationError) as exc_info:
            TelegramMessage.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("chat", "type")
        assert errors[0]["type"] == "missing"


class TestTelegramUpdate:
    def test_telegram_update_valid_data(self):
        """Verify that TelegramUpdate instantiates correctly with nested message."""
        data = {
            "update_id": 10,
            "message": {
                "message_id": 534,
                "date": 45623,
                "chat": {"id": 34534, "type": "public"},
                "from": {"id": 3456234, "is_bot": False, "first_name": "foo"},
                "photo": [
                    {
                        "file_id": "23fsf23f",
                        "file_unique_id": "fdsf23r",
                        "width": 100,
                        "height": 100,
                        "file_size": 34,
                    }
                ],
            },
        }

        msg = TelegramUpdate.model_validate(data)

        assert msg.update_id == 10
        assert isinstance(msg.message, TelegramMessage)
        assert msg.message.message_id == 534

    def test_telegram_update_optional_message_defaults_to_none(self):
        """Verify that message defaults to None when omitted (e.g., inline queries)."""
        data = {"update_id": 99}

        update = TelegramUpdate.model_validate(data)

        assert update.update_id == 99
        assert update.message is None

    def test_telegram_update_missing_update_id(self):
        """Verify that ValidationError is raised when update_id is missing."""
        data = {
            "message": {
                "message_id": 1,
                "date": 1700000000,
                "chat": {"id": 1, "type": "private"},
                "from": {"id": 1, "is_bot": False, "first_name": "A"},
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            TelegramUpdate.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("update_id",)
        assert errors[0]["type"] == "missing"

    def test_telegram_update_invalid_update_id_type(self):
        """Verify that ValidationError is raised when update_id cannot parse to int."""
        data = {"update_id": "not_an_int"}

        with pytest.raises(ValidationError) as exc_info:
            TelegramUpdate.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("update_id",)
        assert errors[0]["type"] == "int_parsing"

    def test_telegram_update_invalid_nested_message(self):
        """Verify that validation errors bubble up from nested message with proper location tuple."""
        data = {
            "update_id": 10,
            "message": {
                "message_id": 1,
                "date": 1700000000,
                "chat": {"id": 1},  # missing 'type'
                "from": {"id": 1, "is_bot": False, "first_name": "A"},
            },
        }

        with pytest.raises(ValidationError) as exc_info:
            TelegramUpdate.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("message", "chat", "type")
        assert errors[0]["type"] == "missing"

    def test_telegram_update_minimal_valid(self):
        """Verify that minimal valid update (only update_id) parses correctly."""
        data = {"update_id": 1}

        update = TelegramUpdate.model_validate(data)

        assert update.update_id == 1
        assert update.message is None
