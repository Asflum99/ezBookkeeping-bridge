import base64
import json
import os

from groq import Groq


def cargar_prompt_sistema(nombre_archivo: str) -> str:
    """Lee el contenido de un archivo de prompt en la carpeta prompts/"""
    ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta_prompt = os.path.join(ruta_base, "prompts", nombre_archivo)

    with open(ruta_prompt, "r", encoding="utf-8") as archivo:
        return archivo.read()


def procesar_gasto_con_ia(ruta_foto_local: str) -> dict:
    with open(ruta_foto_local, "rb") as image_file:
        imagen_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    client = Groq()

    try:
        system_prompt = cargar_prompt_sistema("sistema_extractor.md")

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

        if datos := chat_completion.choices[0].message.content:
            return json.loads(datos)
        else:
            raise Exception

    except FileNotFoundError as e:
        print(
            f"❌ ERROR CRÍTICO DE INFRAESTRUCTURA: No se encontró el archivo de prompt de la IA. {e}"
        )
        raise e

    except Exception as e:
        print(f"❌ Error general al conectar con Groq: {e}")
        raise e
