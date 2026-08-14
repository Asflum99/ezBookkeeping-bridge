from datetime import datetime, timedelta
from typing import cast

import pytest
from helpers import VALID_USER_INFO

from config import settings
from formatter import (
    get_transfer_category_id,
    prepare_confirmation_message,
    resolve_transaction_type,
    validate_and_sanitize_voucher_data,
)

VALID_HINTS = cast(
    list[tuple[str, str, int]],
    VALID_USER_INFO["cuentas_hints"],
)
VALID_CATEGORIES = cast(dict[str, str], VALID_USER_INFO["categorias"])


class TestValidateAndSanitizeVoucherData:
    """Unit tests for validating and sanitizing LLM extracted voucher data."""

    def test_valid_data_passes_through(self):
        yesterday_str = (datetime.now(settings.timezone) - timedelta(days=1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        data = {
            "amount": 25,
            "date_time": yesterday_str,
            "payment_account": "billetera_digital",
            "category": "Comida",
        }

        user_info = {
            "nombre": "Test User",
            "ez_token": "fake-jwt-token",
            "cuentas": {"BCP": "3826102909318201344"},
        }

        user_accounts_hints = [("BCP", "Yape, BCP Transfer, morado", 2)]

        user_categories = {"Comida": "3826101146502561820"}

        result = validate_and_sanitize_voucher_data(
            data, user_info, user_accounts_hints, user_categories
        )

        assert result["amount"] == 25
        assert result["date_time"] == yesterday_str

    @pytest.mark.parametrize(
        "invalid_payload",
        [
            {
                "amount": None,
                "date_time": "2026-07-19 12:00:00",
                "payment_account": "billetera_digital",
                "category": "Comida",
            },
            {
                "amount": 0,
                "date_time": "2026-07-19 12:00:00",
                "payment_account": "billetera_digital",
                "category": "Comida",
            },
            {
                "amount": -15.50,
                "date_time": "2026-07-19 12:00:00",
                "payment_account": "billetera_digital",
                "category": "Comida",
            },
            {"date_time": "2026-07-19 12:00:00"},
        ],
        ids=[
            "amount_is_none",
            "amount_is_zero",
            "amount_is_negative",
            "amount_is_missing",
        ],
    )
    def test_invalid_amount_raises_value_error(self, invalid_payload):
        """Verify that missing, zero, or None amounts raise a ValueError."""
        with pytest.raises(ValueError):
            validate_and_sanitize_voucher_data(
                invalid_payload, VALID_USER_INFO, VALID_HINTS, VALID_CATEGORIES
            )

    def test_missing_date_falls_back(self):
        data = {
            "amount": 25,
            "date_time": "",
            "payment_account": "billetera_digital",
            "category": "Comida",
        }

        user_info = {
            "nombre": "Test User",
            "ez_token": "fake-jwt-token",
            "cuentas": {"BCP": "3826102909318201344"},
        }

        user_accounts_hints = [("BCP", "Yape, BCP Transfer, morado", 2)]

        user_categories = {"Comida": "3826101146502561820"}

        result = validate_and_sanitize_voucher_data(
            data, user_info, user_accounts_hints, user_categories
        )

        assert "date_time" in result
        assert datetime.strptime(result["date_time"], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=settings.timezone
        )

    def test_date_out_of_range_falls_back(self):
        old_date = (datetime.now(settings.timezone) - timedelta(days=30)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        data = {
            "date_time": old_date,
            "amount": 10,
            "payment_account": "billetera_digital",
            "category": "Comida",
        }

        user_info = {
            "nombre": "Test User",
            "ez_token": "fake-jwt-token",
            "cuentas": {"BCP": "3826102909318201344"},
        }

        user_accounts_hints = [("BCP", "Yape, BCP Transfer, morado", 2)]

        user_categories = {"Comida": "3826101146502561820"}

        result = validate_and_sanitize_voucher_data(
            data, user_info, user_accounts_hints, user_categories
        )

        assert result["date_time"] != old_date

    def test_future_date_falls_back(self):
        future_date = (datetime.now(settings.timezone) + timedelta(days=7)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        data = {
            "date_time": future_date,
            "amount": 10,
            "payment_account": "billetera_digital",
            "category": "Comida",
        }

        user_info = {
            "nombre": "Test User",
            "ez_token": "fake-jwt-token",
            "cuentas": {"BCP": "3826102909318201344"},
        }

        user_accounts_hints = [("BCP", "Yape, BCP Transfer, morado", 2)]

        user_categories = {"Comida": "3826101146502561820"}

        result = validate_and_sanitize_voucher_data(
            data, user_info, user_accounts_hints, user_categories
        )

        assert result["date_time"] != future_date

    @pytest.mark.parametrize(
        "invalid_date",
        ["not-a-date", 123],
        ids=["string_format", "non_string_type"],
    )
    def test_invalid_date_format_falls_back(self, invalid_date):
        """Verify that malformed or non-string dates fall back to a valid date string."""
        data = {
            "date_time": invalid_date,
            "amount": 10,
            "payment_account": "billetera_digital",
            "category": "Comida",
        }

        result = validate_and_sanitize_voucher_data(
            data, VALID_USER_INFO, VALID_HINTS, VALID_CATEGORIES
        )

        assert datetime.strptime(result["date_time"], "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=settings.timezone
        )

    def test_does_not_mutate_original(self):
        """Verify that the original input dictionary is not modified (immutability)."""
        original = {
            "date_time": "invalid",
            "amount": 10,
            "payment_account": "billetera_digital",
            "category": "Comida",
        }

        user_info = {
            "nombre": "Test User",
            "ez_token": "fake-jwt-token",
            "cuentas": {"BCP": "3826102909318201344"},
        }

        user_accounts_hints = [("BCP", "Yape, BCP Transfer, morado", 2)]

        user_categories = {"Comida": "3826101146502561820"}

        validate_and_sanitize_voucher_data(
            original, user_info, user_accounts_hints, user_categories
        )

        assert original["date_time"] == "invalid"
        assert "comment" not in original

    @pytest.mark.parametrize(
        "invalid_payment_account",
        [None, "", 0],
        ids=["none", "empty_string", "zero"],
    )
    def test_missing_payment_account_raises_value_error(self, invalid_payment_account):
        """Verify that missing, empty, or falsy payment_account raises a ValueError."""
        data = {
            "amount": 10,
            "date_time": "2026-07-19 12:00:00",
            "payment_account": invalid_payment_account,
            "category": "Comida",
        }

        with pytest.raises(ValueError, match="Payment method is required"):
            validate_and_sanitize_voucher_data(
                data, VALID_USER_INFO, VALID_HINTS, VALID_CATEGORIES
            )

    @pytest.mark.parametrize(
        "invalid_category",
        [None, "", 0],
        ids=["none", "empty_string", "zero"],
    )
    def test_missing_category_raises_value_error(self, invalid_category):
        """Verify that missing, empty, or falsy category raises a ValueError."""
        data = {
            "amount": 10,
            "date_time": "2026-07-19 12:00:00",
            "payment_account": "billetera_digital",
            "category": invalid_category,
        }

        with pytest.raises(ValueError, match="Category is required"):
            validate_and_sanitize_voucher_data(
                data, VALID_USER_INFO, VALID_HINTS, VALID_CATEGORIES
            )

    def test_missing_comment_defaults_to_empty_string(self):
        """Verify that missing comment defaults to empty string."""
        now_str = datetime.now(settings.timezone).strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "amount": 10,
            "date_time": now_str,
            "payment_account": "billetera_digital",
            "category": "Comida",
        }

        user_info = {
            "nombre": "Test User",
            "ez_token": "fake-jwt-token",
            "cuentas": {"BCP": "3826102909318201344"},
        }

        user_accounts_hints = [("BCP", "Yape, BCP Transfer, morado", 2)]

        user_categories = {"Comida": "3826101146502561820"}

        result = validate_and_sanitize_voucher_data(
            data, user_info, user_accounts_hints, user_categories
        )

        assert result["comment"] == ""


class TestPrepareConfirmationMessage:
    """Group all unit tests for the confirmation message formatter."""

    def test_basic_message(self):
        data = {
            "amount": 25.50,
            "comment": "Almuerzo",
            "date_time": "2026-07-19 12:30:00",
            "payment_account": "billetera_digital",
            "category": "Comida",
        }
        msg = prepare_confirmation_message(data)

        assert "25.5" in msg
        assert "Almuerzo" in msg
        assert "Comida" in msg

    def test_missing_fields_use_defaults(self):
        msg = prepare_confirmation_message({"amount": 10})
        assert "Desconocido" in msg

    def test_unknown_payment_account(self):
        data = {"amount": 10, "payment_account": "efectivo"}
        msg = prepare_confirmation_message(data)
        assert "efectivo" in msg


class TestResolveTransactionType:
    """Tests for resolve_transaction_type function."""

    def test_type_4_with_hint_match(self):
        hints = [("tarjeta_ripley", "Ripley, 4821, tarjeta", 3)]
        result = resolve_transaction_type([3, 4], "4821", hints)
        assert result == 4

    def test_type_4_no_hint_match(self):
        hints = [("tarjeta_ripley", "Ripley, 4821, tarjeta", 3)]
        result = resolve_transaction_type([3, 4], "9999", hints)
        assert result == 3

    def test_type_4_no_destination_account(self):
        hints = [("tarjeta_ripley", "Ripley, 4821, tarjeta", 3)]
        result = resolve_transaction_type([3, 4], None, hints)
        assert result == 3

    def test_type_3_only(self):
        hints = [("tarjeta_ripley", "Ripley, 4821, tarjeta", 3)]
        result = resolve_transaction_type([3], "4821", hints)
        assert result == 3


class TestGetTransferCategoryId:
    """Tests for get_transfer_category_id function."""

    def test_credit_card_destination(self):
        categories = {
            "Transferencia Bancaria": "123",
            "Pago de Tarjetas de Crédito": "456",
        }
        result = get_transfer_category_id(3, categories)
        assert result == "456"

    def test_other_destination(self):
        categories = {
            "Transferencia Bancaria": "123",
            "Pago de Tarjetas de Crédito": "456",
        }
        result = get_transfer_category_id(2, categories)
        assert result == "123"

    def test_default_category(self):
        categories = {"Transferencia Bancaria": "123"}
        result = get_transfer_category_id(0, categories)
        assert result == "123"


class TestValidateType4Transfer:
    """Tests for type 4 transfer validation."""

    def test_type_4_skips_category_requirement(self):
        now_str = datetime.now(settings.timezone).strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "amount": 100,
            "date_time": now_str,
            "payment_account": "billetera_digital",
            "types": [3, 4],
            "destination_account": "4821",
        }

        result = validate_and_sanitize_voucher_data(
            data, VALID_USER_INFO, VALID_HINTS, VALID_CATEGORIES
        )

        assert result["transaction_type"] == 4
        assert result["category"] is None
        assert result["destination_account_id"] == "3826102909318201345"
        assert result["category_id"] == None

    def test_type_3_requires_category(self):
        now_str = datetime.now(settings.timezone).strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "amount": 100,
            "date_time": now_str,
            "payment_account": "billetera_digital",
            "types": [3],
        }

        with pytest.raises(ValueError, match="Category is required"):
            validate_and_sanitize_voucher_data(
                data, VALID_USER_INFO, VALID_HINTS, VALID_CATEGORIES
            )
