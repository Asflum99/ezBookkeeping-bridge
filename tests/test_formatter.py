from datetime import datetime, timedelta

import pytest

from utils.formatter import (
    prepare_confirmation_message,
    validate_and_sanitize_voucher_data,
)


class TestValidateAndSanitizeVoucherData:
    """Unit tests for validating and sanitizing LLM extracted voucher data."""

    def test_valid_data_passes_through(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "amount": 25,
            "date_time": now_str,
            "payment_method": "billetera_digital",
            "category": "Comida",
        }

        result = validate_and_sanitize_voucher_data(data)

        assert result["amount"] == 25
        assert result["date_time"] == now_str

    @pytest.mark.parametrize(
        "invalid_payload",
        [
            {
                "amount": None,
                "date_time": "2026-07-19 12:00:00",
                "payment_method": "billetera_digital",
                "category": "Comida",
            },
            {
                "amount": 0,
                "date_time": "2026-07-19 12:00:00",
                "payment_method": "billetera_digital",
                "category": "Comida",
            },
            {
                "amount": -15.50,
                "date_time": "2026-07-19 12:00:00",
                "payment_method": "billetera_digital",
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
            validate_and_sanitize_voucher_data(invalid_payload)

    def test_missing_date_falls_back(self):
        data = {
            "date_time": None,
            "amount": 10,
            "payment_method": "billetera_digital",
            "category": "Comida",
        }

        result = validate_and_sanitize_voucher_data(data)

        assert "date_time" in result
        assert datetime.strptime(result["date_time"], "%Y-%m-%d %H:%M:%S")

    def test_date_out_of_range_falls_back(self):
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "date_time": old_date,
            "amount": 10,
            "payment_method": "billetera_digital",
            "category": "Comida",
        }

        result = validate_and_sanitize_voucher_data(data)

        assert result["date_time"] != old_date

    def test_future_date_falls_back(self):
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "date_time": future_date,
            "amount": 10,
            "payment_method": "billetera_digital",
            "category": "Comida",
        }

        result = validate_and_sanitize_voucher_data(data)

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
            "payment_method": "billetera_digital",
            "category": "Comida",
        }

        result = validate_and_sanitize_voucher_data(data)

        assert datetime.strptime(result["date_time"], "%Y-%m-%d %H:%M:%S")

    def test_does_not_mutate_original(self):
        """Verify that the original input dictionary is not modified (immutability)."""
        original = {
            "date_time": "invalid",
            "amount": 10,
            "payment_method": "billetera_digital",
            "category": "Comida",
        }

        validate_and_sanitize_voucher_data(original)

        assert original["date_time"] == "invalid"
        assert "comment" not in original

    @pytest.mark.parametrize(
        "invalid_payment_method",
        [None, "", 0],
        ids=["none", "empty_string", "zero"],
    )
    def test_missing_payment_method_raises_value_error(self, invalid_payment_method):
        """Verify that missing, empty, or falsy payment_method raises a ValueError."""
        data = {
            "amount": 10,
            "date_time": "2026-07-19 12:00:00",
            "payment_method": invalid_payment_method,
            "category": "Comida",
        }

        with pytest.raises(ValueError, match="Payment method is required"):
            validate_and_sanitize_voucher_data(data)

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
            "payment_method": "billetera_digital",
            "category": invalid_category,
        }

        with pytest.raises(ValueError, match="Category is required"):
            validate_and_sanitize_voucher_data(data)

    def test_missing_comment_defaults_to_empty_string(self):
        """Verify that missing comment defaults to empty string."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "amount": 10,
            "date_time": now_str,
            "payment_method": "billetera_digital",
            "category": "Comida",
        }

        result = validate_and_sanitize_voucher_data(data)

        assert result["comment"] == ""


class TestPrepareConfirmationMessage:
    """Group all unit tests for the confirmation message formatter."""

    def test_basic_message(self):
        data = {
            "amount": 25.50,
            "comment": "Almuerzo",
            "date_time": "2026-07-19 12:30:00",
            "payment_method": "billetera_digital",
            "category": "Comida",
        }
        msg = prepare_confirmation_message(data)

        assert "25.5" in msg
        assert "Almuerzo" in msg
        assert "Comida" in msg

    def test_missing_fields_use_defaults(self):
        msg = prepare_confirmation_message({"amount": 10})
        assert "Desconocido" in msg

    def test_unknown_payment_method(self):
        data = {"amount": 10, "payment_method": "efectivo"}
        msg = prepare_confirmation_message(data)
        assert "Desconocido" in msg
