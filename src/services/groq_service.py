import base64
import json
import logging
import os

from groq import Groq

logger = logging.getLogger("bot_finanzas")


def load_system_prompt(user_categories: list[str]) -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "../templates/voucher_prompt.md")

    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt_template = file.read()

    formatted_categories = "\n".join(f"- {cat}" for cat in user_categories)

    return prompt_template.format(categories_list=formatted_categories)


def procesar_gasto_con_ia(ruta_foto_local: str, user_categories: list[str]) -> dict:
    logger.info(
        f"Iniciando procesamiento de voucher con IA (Archivo: {os.path.basename(ruta_foto_local)})"
    )
    with open(ruta_foto_local, "rb") as image_file:
        imagen_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    client = Groq()

    try:
        system_prompt = load_system_prompt(user_categories)

        logger.debug("Enviando petición a la API de Groq...")
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extrae los datos de este voucher de pago.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{imagen_base64}"
                            },
                        },
                    ],
                },
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            response_format={"type": "json_object"},
        )

        if datos_str := chat_completion.choices[0].message.content:
            datos_dict: dict = json.loads(datos_str)

            logger.info("Groq extrajo los datos del voucher con éxito.")
            logger.debug(
                f"JSON crudo devuelto por la IA:\n{json.dumps(datos_dict, indent=2)}"
            )

            return datos_dict
        else:
            raise ValueError(
                "La API de Groq devolvió una respuesta con contenido vacío."
            )

    except FileNotFoundError:
        logger.exception(
            "❌ ERROR CRÍTICO DE INFRAESTRUCTURA: No se encontró el archivo de prompt de la IA."
        )
        raise
    except ValueError:
        logger.exception("❌ La IA no devolvió datos legibles.")
        raise

    except Exception:
        logger.exception("❌ Error general al conectar con Groq")
        raise
