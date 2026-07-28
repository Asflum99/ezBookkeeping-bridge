import httpx
import pytest
import respx

from services.ezbookkeeping_service import register_transaction


class TestRegisterTransaction:
    VALID_SANITIZED_DATA = {
        "amount": 25.50,
        "date_time": "2026-07-19 12:30:00",
        "payment_method": "billetera_digital",
        "category": "Comida",
        "comment": "Tambo",
    }

    VALID_USER_INFO = {
        "ez_token": "fake-jwt-token",
        "cuentas": {"billetera_digital": "3826102909318201344"},
        "categorias": {"Comida": "3826101146502561820"},
    }

    @pytest.fixture(autouse=True)
    def mock_ezbookkeeping_url(self, monkeypatch):
        monkeypatch.setattr(
            "services.ezbookkeeping_service.EZBOOKKEEPING_URL", "http://test"
        )

    @pytest.mark.parametrize(
        "sanitized_data, user_info",
        [
            (
                {"payment_method": "billetera_digital"},
                {
                    "categorias": {"Comida": "123"},
                    "cuentas": {"billetera_digital": "321"},
                },
            ),
            (
                {"category": "Ropa", "payment_method": "billetera_digital"},
                {
                    "categorias": {"Comida": "123"},
                    "cuentas": {"billetera_digital": "321"},
                },
            ),
        ],
        ids=["missing_category", "category_not_in_user_categories"],
    )
    async def test_category_lookup_fails(self, sanitized_data, user_info):
        result = await register_transaction(sanitized_data, user_info)
        assert result is False

    @pytest.mark.parametrize(
        "sanitized_data, user_info",
        [
            (
                {"category": "Comida"},
                {"categorias": {"Comida": "123"}},
            ),
            (
                {"category": "Comida", "payment_method": "efectivo"},
                {
                    "categorias": {"Comida": "123"},
                    "cuentas": {"billetera_digital": "321"},
                },
            ),
        ],
        ids=["missing_payment_method", "payment_method_not_in_user_accounts"],
    )
    async def test_account_lookup_fails(self, sanitized_data, user_info):
        result = await register_transaction(sanitized_data, user_info)
        assert result is False

    @respx.mock
    async def test_success(self):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is True

    @respx.mock
    async def test_api_returns_non_200(self):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(400, json={"success": False})
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is False

    @respx.mock
    async def test_api_returns_200_but_not_success(self):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(200, json={"success": False})
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is False

    @respx.mock
    async def test_api_returns_200_but_invalid_json(self):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(200, text="not json")
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is False

    @respx.mock
    async def test_network_error(self):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is False
