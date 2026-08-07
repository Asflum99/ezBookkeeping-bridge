import base64
import os
import re
from functools import lru_cache
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda

from config import logger, settings


def build_system_prompt(
    user_categories: list[str], user_accounts: list[tuple[str, str]]
) -> str:
    """Format the cached prompt template with user categories."""
    formatted_categories = "\n".join(f"- {cat}" for cat in user_categories)
    formatted_accounts = "\n".join(
        f'- "{name}": Matches {hints}' for name, hints in user_accounts
    )
    logger.debug(f"Rendered accounts in prompt:\n{formatted_accounts}")
    return settings.system_prompt_template.format(
        categories_list=formatted_categories, accounts_list=formatted_accounts
    )


_PROVIDER_MAP = {
    "groq": "groq",
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "google_genai",
}


@lru_cache(1)
def _get_llm():
    """Factory: return configured LLM via init_chat_model."""
    provider = _PROVIDER_MAP.get(settings.llm_provider)
    if not provider:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    try:
        return init_chat_model(
            settings.llm_model,
            model_provider=provider,
            temperature=0.0,
            api_key=settings.llm_api_key,
        )
    except ModuleNotFoundError:
        raise RuntimeError(
            f"Missing dependency for LLM provider '{settings.llm_provider}'. "
            f'Install it with: uv pip install -e ".[{settings.llm_provider}]"'
        )


_PARSER = JsonOutputParser()

_THINKING_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text) -> str:
    """Remove reasoning model thinking blocks before JSON parsing."""
    if hasattr(text, "content"):
        text = text.content
    return _THINKING_RE.sub("", text).strip()


def _encode_image(local_photo_path: str) -> str:
    """Read image file and return base64-encoded string."""
    with open(local_photo_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _build_messages(base64_image: str, system_prompt: str) -> list:
    """Build LangChain message list for vision model."""
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Extract the structured data from this payment voucher.",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        ),
    ]


def process_expense_with_ai(
    local_photo_path: str,
    user_categories: list[str],
    user_accounts: list[tuple[str, str]],
) -> dict[str, Any]:
    """
    Encodes the local voucher image to base64, sends it to the LLM via LangChain
    along with the dynamic system prompt, and returns the parsed JSON extraction.
    """
    filename = os.path.basename(local_photo_path)
    logger.info(f"Starting voucher processing with AI (File: {filename})")

    try:
        base64_image = _encode_image(local_photo_path)
    except FileNotFoundError:
        logger.error(f"❌ Local voucher file not found at: {local_photo_path}")
        raise

    try:
        system_prompt_text = build_system_prompt(user_categories, user_accounts)
        messages = _build_messages(base64_image, system_prompt_text)

        logger.debug("Sending payload to Vision Model via LangChain...")

        chain = _get_llm() | RunnableLambda(_strip_thinking) | _PARSER

        parsed_data: dict[str, Any] = chain.invoke(messages)

        logger.info("Successfully extracted voucher data via LangChain.")
        return parsed_data

    except Exception as e:
        logger.exception(f"❌ Failure during LangChain execution: {e}")
        raise
