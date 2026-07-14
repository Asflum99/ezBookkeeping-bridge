import base64
import json
import logging
import os
from typing import Any

from groq import Groq

logger = logging.getLogger("bot_finanzas")


def load_system_prompt(user_categories: list[str]) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "../templates/voucher_prompt.md")

    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()

    formatted_categories = "\n".join(f"- {cat}" for cat in user_categories)

    return prompt_template.format(categories_list=formatted_categories)


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
        system_prompt = load_system_prompt(user_categories)

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

    except FileNotFoundError:
        logger.exception(
            "❌ CRITICAL INFRASTRUCTURE ERROR: System prompt Markdown template not found."
        )
        raise
    except json.JSONDecodeError as e:
        logger.exception(f"❌ Failed to decode JSON from LLM response. Error: {e}")
        raise ValueError("The IA did not return a valid JSON structure.") from e
    except Exception as e:
        logger.exception(f"❌ General failure while connecting to Groq API: {e}")
        raise
