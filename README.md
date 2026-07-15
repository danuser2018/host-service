# Host Service (host-service)

`host-service` es un microservicio diseñado para actuar como una **Capa de Abstracción del Sistema Operativo** (Host Abstraction Layer - HAL) en el ecosistema Nova-2. Expone una API REST local estable que encapsula el acceso a operaciones físicas del host (como la gestión del volumen de audio), evitando que los contenedores Docker o plugins ejecuten scripts/comandos directamente en la máquina host.

---

## Características

- **FastAPI**: Backend ligero y rápido.
- **Acceso a pactl**: Controla el volumen y el estado de silencio mediante subprocesos efímeros invocando la utilidad nativa de PulseAudio/PipeWire.
- **Validación robusta**: Gestión unificada de tipos de datos de entrada y restricción de volumen al rango `0-100` mediante Pydantic.
- **Seguridad**: Ejecutado como un servicio systemd de usuario (`systemd --user`) con los privilegios mínimos requeridos para acceder a la sesión de audio del usuario actual.

---

## Configuración y Variables de Entorno

El servicio carga su configuración utilizando variables de entorno. Puedes declarar las siguientes variables en un archivo `.env` en la raíz del proyecto o pasarlas al proceso:

| Variable | Tipo | Por Defecto | Descripción |
|---|---|---|---|
| `HOST` | `str` | `0.0.0.0` | Dirección IP de red a la que se vincula el servidor |
| `PORT` | `int` | `8007` | Puerto en el que escucha el servidor |
| `LOG_LEVEL` | `str` | `INFO` | Nivel de logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

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
