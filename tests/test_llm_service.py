import base64

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from services.llm_service import (
    _build_messages,
    _encode_image,
    _get_llm,
    _strip_thinking,
    build_system_prompt,
    process_expense_with_ai,
)


class TestBuildSystemPrompt:
    def test_single_category(self):
        result = build_system_prompt(["Comida"])

        assert "- Comida" in result
        assert "Allowed Categories" in result

    def test_multiple_categories(self):
        result = build_system_prompt(["Comida", "Ropa", "Transporte"])

        assert "- Comida" in result
        assert "- Ropa" in result
        assert "- Transporte" in result

    def test_empty_categories(self):
        result = build_system_prompt([])

        assert "{categories_list}" not in result
        assert "Allowed Categories" in result

    def test_special_characters(self):
        result = build_system_prompt(["Café & Té", "Niños"])

        assert "- Café & Té" in result
        assert "- Niños" in result


class TestGetLlm:
    @pytest.fixture(autouse=True)
    def _mock_provider_modules(self, mocker):
        """Ensure provider imports resolve to mocks even without real packages."""
        modules_to_mock = [
            "langchain_groq",
            "langchain_openai",
            "langchain_anthropic",
            "langchain_google_genai",
        ]

        mock_sys_modules = {
            mod_name: mocker.MagicMock() for mod_name in modules_to_mock
        }

        mocker.patch.dict("sys.modules", mock_sys_modules)

        yield

        _get_llm.cache_clear()

    def test_groq_provider(self, monkeypatch, mocker):
        monkeypatch.setattr("services.llm_service.LLM_PROVIDER", "groq")
        monkeypatch.setattr("services.llm_service.LLM_MODEL", "test-model")
        monkeypatch.setattr("services.llm_service.LLM_API_KEY", "test-key")

        mock_groq = mocker.patch("langchain_groq.ChatGroq")
        mock_groq.return_value = mocker.MagicMock()

        _get_llm()

        mock_groq.assert_called_once_with(
            model="test-model", temperature=0.0, api_key="test-key"
        )

    def test_openai_provider(self, monkeypatch, mocker):
        monkeypatch.setattr("services.llm_service.LLM_PROVIDER", "openai")
        monkeypatch.setattr("services.llm_service.LLM_MODEL", "test-model")
        monkeypatch.setattr("services.llm_service.LLM_API_KEY", "test-key")

        mock_openai = mocker.patch("langchain_openai.ChatOpenAI")
        mock_openai.return_value = mocker.MagicMock()

        _get_llm()

        mock_openai.assert_called_once_with(
            model="test-model", temperature=0.0, api_key="test-key"
        )

    def test_anthropic_provider(self, monkeypatch, mocker):
        monkeypatch.setattr("services.llm_service.LLM_PROVIDER", "anthropic")
        monkeypatch.setattr("services.llm_service.LLM_MODEL", "test-model")
        monkeypatch.setattr("services.llm_service.LLM_API_KEY", "test-key")

        mock_anthropic = mocker.patch("langchain_anthropic.ChatAnthropic")
        mock_anthropic.return_value = mocker.MagicMock()

        _get_llm()

        mock_anthropic.assert_called_once_with(
            model="test-model", temperature=0.0, api_key="test-key"
        )

    def test_gemini_provider(self, monkeypatch, mocker):
        monkeypatch.setattr("services.llm_service.LLM_PROVIDER", "gemini")
        monkeypatch.setattr("services.llm_service.LLM_MODEL", "test-model")
        monkeypatch.setattr("services.llm_service.LLM_API_KEY", "test-key")

        mock_gemini = mocker.patch("langchain_google_genai.ChatGoogleGenerativeAI")
        mock_gemini.return_value = mocker.MagicMock()

        _get_llm()

        mock_gemini.assert_called_once_with(
            model="test-model", temperature=0.0, google_api_key="test-key"
        )

    def test_unsupported_provider(self, monkeypatch):
        monkeypatch.setattr("services.llm_service.LLM_PROVIDER", "unsupported")

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            _get_llm()


class TestStripThinking:
    def test_removes_think_block(self):
        text = "{\"amount\": 3}"
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
        msg = AIMessage(content="<think>reasoning</think>\n{\"amount\": 3}")
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
            process_expense_with_ai("/nonexistent/path.jpg", ["Comida"])

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

        result = process_expense_with_ai(str(image_file), ["Comida", "Ropa"])

        assert result == {"amount": 100}
        final_parser.invoke.assert_called_once()
        messages = final_parser.invoke.call_args[0][0]
        assert isinstance(messages[0], SystemMessage)
        assert "Comida" in messages[0].content
        assert "Ropa" in messages[0].content
