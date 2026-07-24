import base64
import json
import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

from config import LLM_MODEL, PROJECT_ROOT, logger

_PROMPT_TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "templates", "voucher_prompt.md")

try:
    with open(_PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as _f:
        _SYSTEM_PROMPT_TEMPLATE = _f.read()
except FileNotFoundError:
    logger.critical(
        f"❌ CRITICAL: System prompt template not found at {_PROMPT_TEMPLATE_PATH}. "
        "The application cannot start without it."
    )
    raise


def build_system_prompt(user_categories: list[str]) -> str:
    """Format the cached prompt template with user categories."""
    formatted_categories = "\n".join(f"- {cat}" for cat in user_categories)
    return _SYSTEM_PROMPT_TEMPLATE.format(categories_list=formatted_categories)


def process_expense_with_ai(
    local_photo_path: str, user_categories: list[str]
) -> dict[str, Any]:
    """
    Encodes the local voucher image to base64, sends it to the LLM via LangChain
    along with the dynamic system prompt, and returns the parsed JSON extraction.
    """
    filename = os.path.basename(local_photo_path)
    logger.info(f"Starting voucher processing with AI (File: {filename})")

    try:
        with open(local_photo_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        logger.error(f"❌ Local voucher file not found at: {local_photo_path}")
        raise

    try:
        system_prompt_text = build_system_prompt(user_categories)

        llm = ChatGroq(
            model=LLM_MODEL,
            temperature=0.0,
        )

        messages = [
            SystemMessage(content=system_prompt_text),
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

        logger.debug("Sending payload to Vision Model via LangChain...")

        chain = llm | JsonOutputParser()

        parsed_data: dict[str, Any] = chain.invoke(messages)

        logger.info("Successfully extracted voucher data via LangChain.")
        logger.debug(f"Raw JSON returned by LLM:\n{json.dumps(parsed_data, indent=2)}")
        return parsed_data

    except Exception as e:
        logger.exception(f"❌ Failure during LangChain execution: {e}")
        raise
