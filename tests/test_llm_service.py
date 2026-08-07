import base64

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from config import settings
from services.llm_service import (
    _build_messages,
    _encode_image,
    _get_llm,
    _strip_thinking,
    build_system_prompt,
    process_expense_with_ai,
)


class TestBuildSystemPrompt:
    def test_categories_and_accounts_injection(self):
        categories = ["Comida", "Transporte"]
        accounts = [
            ("BCP Débito", "Yape, morado"),
            ("Interbank Débito", "Plin, verde"),
        ]

        result = build_system_prompt(categories, accounts)

        assert "- Comida" in result
        assert "- Transporte" in result
        assert '- "BCP Débito": Matches Yape, morado' in result
        assert '- "Interbank Débito": Matches Plin, verde' in result

        assert "{categories_list}" not in result
        assert "{accounts_list}" not in result

    def test_empty_categories_and_accounts(self):
        result = build_system_prompt([], [])

        assert "{categories_list}" not in result
        assert "{accounts_list}" not in result
        assert "Allowed Categories" in result
        assert "Allowed Payment Accounts" in result

    def test_special_characters_in_accounts_and_hints(self):
        categories = ["Niños"]
        accounts = [("Línea 1 Tren", "Tren Lima, estación & tarjeta")]

        result = build_system_prompt(categories, accounts)

        assert "- Niños" in result
        assert '- "Línea 1 Tren": Matches Tren Lima, estación & tarjeta' in result


class TestGetLlm:
    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        yield
        _get_llm.cache_clear()

    def test_groq_provider(self, monkeypatch, mocker):
        monkeypatch.setattr(settings, "llm_provider", "groq")
        monkeypatch.setattr(settings, "llm_model", "test-model")
        monkeypatch.setattr(settings, "groq_api_key", "test-key")

        mock_init = mocker.patch("services.llm_service.init_chat_model")
        mock_init.return_value = mocker.MagicMock()

        _get_llm()

        mock_init.assert_called_once_with(
            "test-model", model_provider="groq", temperature=0.0, api_key="test-key"
        )

    def test_openai_provider(self, monkeypatch, mocker):
        monkeypatch.setattr(settings, "llm_provider", "openai")
        monkeypatch.setattr(settings, "llm_model", "test-model")
        monkeypatch.setattr(settings, "openai_api_key", "test-key")

        mock_init = mocker.patch("services.llm_service.init_chat_model")
        mock_init.return_value = mocker.MagicMock()

        _get_llm()

        mock_init.assert_called_once_with(
            "test-model", model_provider="openai", temperature=0.0, api_key="test-key"
        )

    def test_anthropic_provider(self, monkeypatch, mocker):
        monkeypatch.setattr(settings, "llm_provider", "anthropic")
        monkeypatch.setattr(settings, "llm_model", "test-model")
        monkeypatch.setattr(settings, "anthropic_api_key", "test-key")

        mock_init = mocker.patch("services.llm_service.init_chat_model")
        mock_init.return_value = mocker.MagicMock()

        _get_llm()

        mock_init.assert_called_once_with(
            "test-model",
            model_provider="anthropic",
            temperature=0.0,
            api_key="test-key",
        )

    def test_gemini_uses_google_genai_provider(self, monkeypatch, mocker):
        monkeypatch.setattr(settings, "llm_provider", "gemini")
        monkeypatch.setattr(settings, "llm_model", "test-model")
        monkeypatch.setattr(settings, "google_api_key", "test-key")

        mock_init = mocker.patch("services.llm_service.init_chat_model")
        mock_init.return_value = mocker.MagicMock()

        _get_llm()

        mock_init.assert_called_once_with(
            "test-model",
            model_provider="google_genai",
            temperature=0.0,
            api_key="test-key",
        )

    def test_unsupported_provider(self, monkeypatch):
        monkeypatch.setattr(settings, "llm_provider", "unsupported")

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            _get_llm()

    def test_missing_provider_module_raises_runtime_error(self, monkeypatch, mocker):
        monkeypatch.setattr(settings, "llm_provider", "groq")
        monkeypatch.setattr(settings, "llm_model", "test-model")
        monkeypatch.setattr(settings, "groq_api_key", "test-key")

        mocker.patch(
            "services.llm_service.init_chat_model",
            side_effect=ModuleNotFoundError("No module named 'langchain_groq'"),
        )

        with pytest.raises(RuntimeError, match="Missing dependency"):
            _get_llm()


class TestStripThinking:
    def test_removes_think_block(self):
        text = '{"amount": 3}'
        result = _strip_thinking(text)
        assert result == '{"amount": 3}'

    def test_passthrough_plain_json(self):
        result = _strip_thinking('{"amount": 3}')
        assert result == '{"amount": 3}'

    def test_handles_aimessage(self):
        msg = AIMessage(content='{"amount": 3}')
        result = _strip_thinking(msg)
        assert result == '{"amount": 3}'

    def test_handles_aimessage_with_think_block(self):
        msg = AIMessage(content='<think>reasoning</think>\n{"amount": 3}')
        result = _strip_thinking(msg)
        assert result == '{"amount": 3}'

    def test_handles_empty_string(self):
        result = _strip_thinking("")
        assert result == ""


class TestEncodeImage:
    def test_encodes_file(self, tmp_path):
        image_file = tmp_path / "test.jpg"
        image_file.write_bytes(b"fake image bytes")

        result = _encode_image(str(image_file))

        assert result == base64.b64encode(b"fake image bytes").decode("utf-8")

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            _encode_image("/nonexistent/path.jpg")

    def test_human_message_image_url(self):
        result = _build_messages("abc123", "system prompt")
        human_content = result[1].content

        text_block = human_content[0]
        assert text_block["type"] == "text"
        assert "Extract" in text_block["text"]

        image_block = human_content[1]
        assert image_block["type"] == "image_url"
        assert "data:image/jpeg;base64,abc123" in image_block["image_url"]["url"]


class TestBuildMessages:
    def test_message_structure(self):
        result = _build_messages("base64data", "system prompt")

        assert len(result) == 2
        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[1], HumanMessage)

    def test_system_message_content(self):
        result = _build_messages("base64data", "system prompt")

        assert result[0].content == "system prompt"

    def test_human_message_image_url(self):
        result = _build_messages("abc123", "system prompt")

        human_content = result[1].content
        image_block = human_content[1]
        assert image_block["type"] == "image_url"
        assert "data:image/jpeg;base64,abc123" in image_block["image_url"]["url"]


class TestProcessExpenseWithAi:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            process_expense_with_ai(
                "/nonexistent/path.jpg",
                ["Comida"],
                [("BCP Débito", "Yape, BCP transfer, morado")],
            )

    def test_calls_llm_with_correct_messages(self, tmp_path, mocker):
        mocker.patch("services.llm_service._PARSER")
        mocker.patch("services.llm_service._encode_image", return_value="base64data")
        mocker.patch("services.llm_service._strip_thinking", side_effect=lambda x: x)

        # Build a mock chain: mock_llm | RunnableLambda(...) | _PARSER
        # The chain invokes mock_llm.__or__(...) then result.__or__(_PARSER)
        final_parser = mocker.MagicMock()
        final_parser.invoke.return_value = {"amount": 100}

        step2 = mocker.MagicMock()
        step2.__or__ = mocker.MagicMock(return_value=final_parser)

        mock_llm = mocker.MagicMock()
        mock_llm.__or__ = mocker.MagicMock(return_value=step2)
        mocker.patch("services.llm_service._get_llm", return_value=mock_llm)

        image_file = tmp_path / "test.jpg"
        image_file.write_bytes(b"fake image")

        result = process_expense_with_ai(
            str(image_file),
            ["Comida", "Ropa"],
            [("BCP Débito", "Yape, BCP transfer, morado")],
        )

        assert result == {"amount": 100}
        final_parser.invoke.assert_called_once()
        messages = final_parser.invoke.call_args[0][0]
        assert isinstance(messages[0], SystemMessage)
        assert "Comida" in messages[0].content
        assert "Ropa" in messages[0].content
        assert "BCP Débito" in messages[0].content
        assert "Yape, BCP transfer, morado" in messages[0].content
