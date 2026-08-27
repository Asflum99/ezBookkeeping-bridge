from typing import ClassVar

import httpx
import pytest
import respx

from services.ezbookkeeping_service import (
    get_user_accounts,
    get_user_categories,
    register_transaction,
)

TRANSFER_SANITIZED_DATA = {
    "amount": 100.00,
    "date_time": "2026-07-19 12:30:00",
    "payment_account": "billetera_digital",
    "category": None,
    "comment": "Pago tarjeta",
    "transaction_type": 4,
    "category_id": "3826101146502561822",
    "destination_account_id": "3826102909318201345",
}

TRANSFER_USER_INFO = {
    "ez_token": "fake-jwt-token",
    "cuentas": {
        "billetera_digital": "3826102909318201344",
        "tarjeta_ripley": "3826102909318201345",
    },
    "categorias": {
        "Transferencia Bancaria": "3826101146502561821",
        "Pago de Tarjetas de Crédito": "3826101146502561822",
    },
}


class TestRegisterTransaction:
    VALID_SANITIZED_DATA: ClassVar = {
        "amount": 25.50,
        "date_time": "2026-07-19 12:30:00",
        "payment_account": "billetera_digital",
        "category": "Comida",
        "comment": "Tambo",
        "transaction_type": 3,
        "category_id": "3826101146502561820",
        "destination_account_id": None,
    }

    VALID_USER_INFO: ClassVar = {
        "ez_token": "fake-jwt-token",
        "cuentas": {"billetera_digital": "3826102909318201344"},
        "categorias": {"Comida": "3826101146502561820"},
    }

    @pytest.mark.parametrize(
        "sanitized_data, user_info",
        [
            (
                {
                    "amount": 10,
                    "date_time": "2026-07-19 12:00:00",
                    "payment_account": "billetera_digital",
                    "transaction_type": 3,
                },
                {
                    "ez_token": "fake-token",
                    "categorias": {"Comida": "123"},
                    "cuentas": {"billetera_digital": "321"},
                },
            ),
            (
                {
                    "amount": 10,
                    "date_time": "2026-07-19 12:00:00",
                    "category": "Ropa",
                    "payment_account": "billetera_digital",
                    "transaction_type": 3,
                    "category_id": "999",
                },
                {
                    "ez_token": "fake-token",
                    "categorias": {"Comida": "123"},
                    "cuentas": {"billetera_digital": "321"},
                },
            ),
        ],
        ids=["missing_category_id", "category_id_not_in_user_categories"],
    )
    async def test_category_lookup_fails(self, sanitized_data, user_info):
        result = await register_transaction(sanitized_data, user_info)
        assert result is False

    @pytest.mark.parametrize(
        "sanitized_data, user_info",
        [
            (
                {
                    "amount": 10,
                    "date_time": "2026-07-19 12:00:00",
                    "category": "Comida",
                    "transaction_type": 3,
                    "category_id": "123",
                },
                {"ez_token": "fake-token", "categorias": {"Comida": "123"}},
            ),
            (
                {
                    "amount": 10,
                    "date_time": "2026-07-19 12:00:00",
                    "category": "Comida",
                    "payment_account": "efectivo",
                    "transaction_type": 3,
                    "category_id": "123",
                },
                {
                    "ez_token": "fake-token",
                    "categorias": {"Comida": "123"},
                    "cuentas": {"billetera_digital": "321"},
                },
            ),
        ],
        ids=["missing_payment_account", "payment_account_not_in_user_accounts"],
    )
    async def test_account_lookup_fails(self, sanitized_data, user_info):
        result = await register_transaction(sanitized_data, user_info)
        assert result is False

    @respx.mock
    async def test_success(self, _mock_ezbookkeeping_url):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is True

    @respx.mock
    async def test_api_returns_non_200(self, _mock_ezbookkeeping_url):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(400, json={"success": False})
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is False

    @respx.mock
    async def test_api_returns_200_but_not_success(self, _mock_ezbookkeeping_url):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(200, json={"success": False})
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is False

    @respx.mock
    async def test_api_returns_200_but_invalid_json(self, _mock_ezbookkeeping_url):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(200, text="not json")
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is False

    @respx.mock
    async def test_network_error(self, _mock_ezbookkeeping_url):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        result = await register_transaction(
            self.VALID_SANITIZED_DATA, self.VALID_USER_INFO
        )

        assert result is False

    @respx.mock
    async def test_type_4_transfer_success(self, _mock_ezbookkeeping_url):
        respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        result = await register_transaction(TRANSFER_SANITIZED_DATA, TRANSFER_USER_INFO)

        assert result is True

    @respx.mock
    async def test_type_4_transfer_includes_destination_fields(
        self, _mock_ezbookkeeping_url
    ):
        mock = respx.post("http://test/api/v1/transactions/add.json").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        await register_transaction(TRANSFER_SANITIZED_DATA, TRANSFER_USER_INFO)

        body = mock.calls[0].request.content
        import json

        payload = json.loads(body)
        assert payload["type"] == 4
        assert payload["destinationAccountId"] == "3826102909318201345"
        assert payload["destinationAmount"] == 10000

    async def test_type_4_missing_destination_fails(self):
        data = {
            "amount": 100,
            "date_time": "2026-07-19 12:00:00",
            "payment_account": "billetera_digital",
            "transaction_type": 4,
            "category_id": "123",
            "destination_account_id": None,
        }
        user_info = {
            "ez_token": "fake-token",
            "cuentas": {"billetera_digital": "321"},
            "categorias": {},
        }

        result = await register_transaction(data, user_info)
        assert result is False


class TestGetUserAccounts:
    @respx.mock
    async def test_success(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/accounts/list.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "result": [
                        {"id": "acc-1", "name": "BCP"},
                        {"id": "acc-2", "name": "Yape"},
                    ],
                },
            )
        )
        result = await get_user_accounts("fake-token")
        assert result == [
            {"id": "acc-1", "name": "BCP"},
            {"id": "acc-2", "name": "Yape"},
        ]

    @respx.mock
    async def test_api_returns_non_200(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/accounts/list.json").mock(
            return_value=httpx.Response(401, json={"success": False})
        )
        result = await get_user_accounts("fake-token")
        assert result is None

    @respx.mock
    async def test_api_returns_success_false(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/accounts/list.json").mock(
            return_value=httpx.Response(200, json={"success": False})
        )
        result = await get_user_accounts("fake-token")
        assert result is None

    @respx.mock
    async def test_network_error(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/accounts/list.json").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        result = await get_user_accounts("fake-token")
        assert result is None


class TestGetUserCategories:
    @respx.mock
    async def test_success_flat_categories(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/transaction/categories/list.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "result": {
                        "1": [{"id": "inc-1", "name": "Salary", "subCategories": []}],
                        "2": [
                            {"id": "exp-1", "name": "Food", "subCategories": []},
                            {"id": "exp-2", "name": "Transport", "subCategories": []},
                        ],
                        "3": [],
                    },
                },
            )
        )
        result = await get_user_categories("fake-token")
        assert result == [
            {"id": "inc-1", "name": "Salary", "type": 1},
            {"id": "exp-1", "name": "Food", "type": 2},
            {"id": "exp-2", "name": "Transport", "type": 2},
        ]

    @respx.mock
    async def test_success_with_subcategories(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/transaction/categories/list.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "result": {
                        "2": [
                            {
                                "id": "exp-1",
                                "name": "Food",
                                "subCategories": [
                                    {"id": "sub-1", "name": "Groceries"},
                                    {"id": "sub-2", "name": "Restaurants"},
                                ],
                            }
                        ],
                    },
                },
            )
        )
        result = await get_user_categories("fake-token")
        assert result == [
            {"id": "exp-1", "name": "Food", "type": 2},
            {"id": "sub-1", "name": "Food > Groceries", "type": 2},
            {"id": "sub-2", "name": "Food > Restaurants", "type": 2},
        ]

    @respx.mock
    async def test_api_returns_non_200(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/transaction/categories/list.json").mock(
            return_value=httpx.Response(401, json={"success": False})
        )
        result = await get_user_categories("fake-token")
        assert result is None

    @respx.mock
    async def test_api_returns_success_false(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/transaction/categories/list.json").mock(
            return_value=httpx.Response(200, json={"success": False})
        )
        result = await get_user_categories("fake-token")
        assert result is None

    @respx.mock
    async def test_network_error(self, _mock_ezbookkeeping_url):
        respx.get("http://test/api/v1/transaction/categories/list.json").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        result = await get_user_categories("fake-token")
        assert result is None
