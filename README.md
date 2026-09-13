# Host Service (host-service)

`host-service` es un microservicio diseñado para actuar como una **Capa de Abstracción del Sistema Operativo** (Host Abstraction Layer - HAL) en el ecosistema Nova-2. Expone una API REST local estable que encapsula el acceso a operaciones físicas del host (como la gestión del volumen de audio) y la **ejecución controlada de aplicaciones locales del sistema operativo** mediante identificadores lógicos canónicos y un catálogo cerrado sin acceso a shell.

---

## Características

- **FastAPI**: Backend asíncrono, ligero y rápido.
- **Acceso a pactl**: Controla el volumen y el estado de silencio mediante subprocesos efímeros invocando la utilidad nativa de PulseAudio/PipeWire.
- **Ejecución Segura de Comandos**: Ejecución de aplicaciones locales registradas mediante identificadores lógicos (`POST /v1/commands/execute`) usando `subprocess.Popen` sin invocación de shell (`shell=False`), desacoplada en una nueva sesión (`start_new_session=True`) y no bloqueante.
- **Catálogo Central Declarativo**: Carga `config/commands.yaml` como fuente única de verdad para definición de comandos (`argv`), niveles de riesgo (`risk`) y frases naturales (`phrases`). Validación estricta con política Fail Closed en el arranque.
- **Distribución Asíncrona vía NATS**: Publicación periódica (arranque y cada 60s) de la proyección pública en `event.host.commands.available` hacia `orchestrator` y `security-service`, eliminando el acoplamiento HTTP directo con `security-service`.
- **Validación robusta y ADR-004**: Tipado y validaciones estrictas con Pydantic v2 y respuestas de error estandarizadas.
- **Seguridad**: Ejecutado como un servicio systemd de usuario (`systemd --user`) con los privilegios del usuario de la sesión activa (`DISPLAY`, `WAYLAND_DISPLAY`, `DBUS_SESSION_BUS_ADDRESS`).

---

## Configuración y Variables de Entorno

El servicio carga su configuración utilizando variables de entorno. Puedes declarar las siguientes variables en un archivo `.env` en la raíz del proyecto o pasarlas al proceso:

| Variable | Tipo | Por Defecto | Descripción |
|---|---|---|---|
| `HOST` | `str` | `0.0.0.0` | Dirección IP de red a la que se vincula el servidor |
| `PORT` | `int` | `8007` | Puerto en el que escucha el servidor |
| `LOG_LEVEL` | `str` | `INFO` | Nivel de logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `NATS_URL` | `str` | `nats://localhost:4222` | URL de conexión al broker NATS |
| `CATALOG_PUBLISH_INTERVAL_SECONDS` | `float` | `60.0` | Intervalo en segundos entre publicaciones del catálogo de comandos |
| `COMMANDS_FILE` | `str` | `config/commands.yaml` | Ruta al fichero YAML centralizado con el catálogo de comandos de Nova |

---

## Endpoints de la API

### 1. GET `/health`
Devuelve el estado de salud básica del microservicio.
- **Respuesta (200 OK):**
```json
{
  "status": "ok"
}
```

### 2. GET `/v1/audio/volume`
Obtiene el volumen actual y el estado de silencio.
- **Respuesta (200 OK):**
```json
{
  "volume": 50,
  "muted": false
}
```

### 3. POST `/v1/audio/volume/set`
Establece un volumen absoluto.
- **Cuerpo de la Petición:**
```json
{
  "volume": 80
}
```
- **Respuesta (200 OK):**
```json
{
  "volume": 80,
  "muted": false
}
```

### 4. POST `/v1/audio/volume/up`
Sube el volumen por pasos (se auto-limita a 100%).
- **Cuerpo de la Petición:**
```json
{
  "step": 5
}
```
- **Respuesta (200 OK):**
```json
{
  "volume": 85,
  "muted": false
}
```

### 5. POST `/v1/audio/volume/down`
Baja el volumen por pasos (se auto-limita a 0%).
- **Cuerpo de la Petición:**
```json
{
  "step": 5
}
```
- **Respuesta (200 OK):**
```json
{
  "volume": 80,
  "muted": false
}
```

### 6. POST `/v1/audio/mute`
Silencia el sonido.
- **Respuesta (200 OK):**
```json
{
  "volume": 80,
  "muted": true
}
```

### 7. POST `/v1/audio/unmute`
Reactiva el sonido.
- **Respuesta (200 OK):**
```json
{
  "volume": 80,
  "muted": false
}
```

### 8. POST `/v1/audio/toggle-mute`
Alterna el estado de silencio.
- **Respuesta (200 OK):**
```json
{
  "volume": 80,
  "muted": true
}
```

### 9. POST `/v1/commands/execute`
Ejecuta de forma desacoplada y no bloqueante un comando local registrado en el catálogo del host mediante su identificador lógico.
- **Cuerpo de la Petición:**
```json
{
  "command": "calculator"
}
```
- **Respuesta Exitosa (200 OK):**
```json
{
  "command": "calculator",
  "status": "started",
  "pid": 48219
}
```
- **Errores Posibles (ADR-004):**
  - `404 Not Found` (`COMMAND_NOT_FOUND`): Comando no registrado en el catálogo.
  - `422 Unprocessable Entity` (`VALIDATION_ERROR`): Carga útil malformada o campo `command` ausente/vacío.
  - `500 Internal Server Error` (`COMMAND_EXECUTION_FAILED`): Error del sistema operativo al lanzar el proceso (ej. binario no encontrado o sin permisos).

---

## Catálogo Centralizado de Comandos (`config/commands.yaml`)

El archivo `config/commands.yaml` actúa como la **fuente única de verdad** (*Single Source of Truth*) para los comandos de Nova, definiendo su identificador lógico (`name`), su vector privado de argumentos físicos (`command` / `argv`), su nivel de riesgo (`risk`) y sus frases de activación en lenguaje natural (`phrases`). El servicio valida este archivo con una política **Fail-Closed** durante el arranque.

```yaml
commands:
  - name: calculator
    command:
      - gnome-calculator
    risk: low
    phrases:
      - calculadora
      - maquina de calcular
      - el programa de cuentas
      - abre la calculadora

  - name: backup
    command:
      - /usr/local/bin/nova-backup
      - --quick
    risk: medium
    phrases:
      - copia de seguridad
      - hacer backup
      - respaldar datos
```

Durante el arranque y de forma periódica (cada 60 segundos por defecto, configurable mediante `CATALOG_PUBLISH_INTERVAL_SECONDS`), `host-service` publica una **proyección pública** a través de NATS en el subject `event.host.commands.available` conteniendo los campos `name`, `risk` y `phrases`. Por aislamiento y seguridad, el ejecutable físico (`command` / `argv`) **nunca** se incluye en la proyección pública distribuida, siendo consumido de forma reactiva y asíncrona por `orchestrator` y `security-service`.

---

## Ejecución en Local

### Requisitos Previos

Asegúrate de que la utilidad `pactl` está instalada en tu sistema (suele venir preinstalada en distros con PipeWire o PulseAudio):
```bash
which pactl
```

### Clonado e Instalación

1. Crea y activa un entorno virtual de Python:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta el servidor manualmente:
```bash
python -m src.main
```

---

## Ejecución de Pruebas

Para ejecutar las pruebas unitarias y de API localmente, asegúrate de tener `pytest` en tu entorno virtual y ejecuta:
```bash
pytest
```
o para obtener cobertura y ver detalles:
```bash
pytest -v
```
Las pruebas unitarias y de API utilizan mocks automáticos de `subprocess.run` para simular las llamadas a `pactl`, garantizando que puedan ejecutarse en cualquier entorno (incluyendo plataformas de CI como GitHub Actions) sin necesidad de tener PulseAudio o PipeWire activos.
