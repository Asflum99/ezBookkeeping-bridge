import base64
import json
import logging
import os

from groq import Groq

logger = logging.getLogger("bot_finanzas")


def _cargar_prompt_sistema(nombre_archivo: str) -> str:
    """Lee el contenido de un archivo de prompt en la carpeta prompts/"""
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_prompt = os.path.join(ruta_base, "config/prompts", nombre_archivo)

    with open(ruta_prompt, "r", encoding="utf-8") as archivo:
        return archivo.read()


def procesar_gasto_con_ia(ruta_foto_local: str) -> dict:
    logger.info(
        f"Iniciando procesamiento de voucher con IA (Archivo: {os.path.basename(ruta_foto_local)})"
    )
    with open(ruta_foto_local, "rb") as image_file:
        imagen_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    client = Groq()

    try:
        system_prompt = _cargar_prompt_sistema("sistema_extractor.md")

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
