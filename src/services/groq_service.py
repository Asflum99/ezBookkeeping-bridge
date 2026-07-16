import base64
import json
import os
from typing import Any

from groq import Groq

from config.logger import logger

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    Encodes the local voucher image to base64, sends it to the Groq Vision model
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

    client = Groq()

    try:
        system_prompt = build_system_prompt(user_categories)

        logger.debug("Sending payload to Groq Vision API...")

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the structured data from this payment voucher.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            response_format={"type": "json_object"},
        )

        response_content = chat_completion.choices[0].message.content

        if response_content:
            parsed_data: dict[str, Any] = json.loads(response_content)

            logger.info("Successfully extracted voucher data from Groq API.")
            logger.debug(
                f"Raw JSON returned by LLM:\n{json.dumps(parsed_data, indent=2)}"
            )
            return parsed_data
        else:
            raise ValueError("Groq API returned an empty message content.")

    except json.JSONDecodeError as e:
        logger.exception(f"❌ Failed to decode JSON from LLM response. Error: {e}")
        raise ValueError("The IA did not return a valid JSON structure.") from e
    except Exception as e:
        logger.exception(f"❌ General failure while connecting to Groq API: {e}")
        raise
