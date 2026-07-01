# Telegram Finance Bot 💰

Un backend ágil y seguro desarrollado con **FastAPI** y gestionado con **uv** para registrar, procesar y categorizar transacciones financieras enviadas directamente desde un bot privado de Telegram.

## 🚀 Características Principales

* **Control de Acceso Estricto**: Filtrado a nivel de Webhook para permitir peticiones únicamente de IDs de Telegram autorizados.
* **Arquitectura Ligera**: Construido sobre FastAPI, garantizando alto rendimiento y baja huella de memoria (ideal para despliegues en contenedores como LXC en Proxmox).
* **Gestión de Entorno Moderna**: Utiliza `uv` para la administración de paquetes a máxima velocidad y `mise` para la gestión de versiones de runtime y automatización de tareas.

---

## 🛠️ Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu máquina de desarrollo:
* **mise** (para gestionar la versión de Python y tareas).
* **uv** (para la gestión rápida de entornos virtuales y dependencias).
* **cloudflared** (CLI de Cloudflare para exponer el entorno local).

---

## ⚙️ Configuración del Entorno

El proyecto utiliza variables de entorno para manejar tokens sensibles y configuraciones de acceso. 

### 1. Variables de Entorno
Crea un archivo de configuración local para `mise` llamado `mise.local.toml` en la raíz del proyecto (este archivo está excluido en el `.gitignore`):

```toml
[env]
TELEGRAM_BOT_TOKEN = "tu_token_secreto_de_botfather"
USUARIOS_PERMITIDOS = "123456789,987654321" # IDs de Telegram separados por comas
```

## Flujo de Desarrollo Local

Para desarrollar y probar el bot en tu máquina local, necesitas levantar el servidor e interconectar Telegram con tu entorno mediante un túnel seguro.

### 1. Levantar el servidor FastAPI

Ejecuta la tarea de desarrollo preconfigurada en el proyecto. Esta tarea arranca el servidor con recarga automática (`--reload`):
```bash
mise run dev
```
*El servidor se quedará escuchando localmente en `http://127.0.0.1:8000`.*

### 2. Abrir el túnel con Cloudflared

Dado que Telegram requiere una URL pública cifrada (HTTPS) para enviar los mensajes, abre otra pestaña de la terminal e inicia el túnel:

```bash
cloudflared tunnel --url http://localhost:8000
```
*Busca en la consola y copia la URL pública generada que termina en `.trycloudflare.com` (ej: `https://abc-123.trycloudflare.com`).*

### 3. Vincular el Bot de Telegram (Set Webhook)
Para finalizar el cableado, debes asociar la URL del túnel al token de tu bot agregando el endpoint `/webhook` al final. Ejecuta el siguiente comando en tu terminal (reemplazando tus credenciales):

```bash
curl -X POST "https://api.telegram.org/bot<TU_TELEGRAM_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://TU_SUBDOMINIO_ALEATORIO.trycloudflare.com/webhook"}'
```

## Verificación y Pruebas

### Comprobar el estado del Webhook

Puedes validar en cualquier momento qué dirección tiene registrada Telegram y si existen errores de entrega ejecutando:

```bash
curl "https://api.telegram.org/bot<TU_TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```
