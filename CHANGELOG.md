# Registro de cambios

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## Guía de uso

Cada versión se documenta bajo su número de versión y fecha de publicación.
Los cambios se agrupan en las siguientes categorías:

- **Añadido** — nuevas funcionalidades.
- **Cambiado** — cambios en funcionalidades existentes.
- **Obsoleto** — funcionalidades que serán eliminadas en versiones futuras.
- **Eliminado** — funcionalidades eliminadas en esta versión.
- **Corregido** — corrección de errores.
- **Seguridad** — correcciones de vulnerabilidades.

## [1.1.0] - 2026-09-11

### Añadido
- Integración con **Security Service** (`security-service`) para la publicación del catálogo de comandos del sistema y sus niveles de riesgo asociados (política `lookup`).
- Fichero de configuración `config/host_commands_risk.yaml` con el catálogo inicial de comandos dinámicos y sus niveles de riesgo (`calculator` [low], `github` [low], `backup` [medium], `format-disk` [high]).
- Módulo `src/services/command_catalog.py`:
  - Función `load_command_catalog`: parseo y carga de comandos desde `config/host_commands_risk.yaml` con fallback automático a `DEFAULT_COMMANDS`.
  - Función asíncrona `publish_command_catalog`: publicación síncrona HTTP mediante `POST /v1/security/tables/host_commands` hacia `security-service`.
- Variable de configuración `SECURITY_SERVICE_BASE_URL` en `src/config.py` (por defecto `http://security-service:8000`).
- Suite de pruebas unitarias en `tests/test_command_catalog.py` para validar la carga de configuración, fallbacks ante ficheros ausentes y la publicación HTTP con manejo de errores.

### Cambiado
- Añadido context manager `lifespan` en `src/app.py` para invocar automáticamente `publish_command_catalog()` durante el arranque del microservicio.
- Incrementada la versión de la aplicación a `1.1.0` en `src/app.py`.

---

## [1.0.0] - 2026-07-15

### Añadido

- Implementación inicial del microservicio FastAPI `host-service` como capa de abstracción del host (HAL) expuesta en el puerto 8007.
- Soporte para consulta y control de volumen absoluto, relativo (pasos de incremento/decremento), silenciado y reactivación del audio utilizando `pactl`.
- Configuración mediante Pydantic Settings con archivo `.env` aislado y validaciones estrictas de rangos de volumen (0-100).
- Suite de pruebas unitarias y de integración con `pytest` y cobertura de endpoints simulando la utilidad `pactl`.
- Configuración de integración continua (CI) mediante una GitHub Action en `.github/workflows/test.yml`.
- Configuración de acceso a las skills de `home-assistant` mediante un enlace simbólico en `.agent/skills`.
- Fichero `CONTRIBUTING.md` con el flujo de trabajo Trunk Based Development, convenciones de commits, guía de Pull Requests y buenas prácticas para desarrollo asistido con IA.
- Fichero `CHANGELOG.md` con el formato Keep a Changelog v1.1.0 en castellano.

### Corregido

- Forzado del locale `LC_ALL=C` en el entorno de ejecución del comando de sistema `pactl` para garantizar una salida en inglés estándar y evitar fallos de parseo en sistemas con locales distintos (como el español "Mute: sí").
- Actualización de los tests unitarios correspondientes para incluir la aserción del paso de la configuración de entorno (`env`).
- Añadido `pytest.ini` con `pythonpath = .` para permitir la ejecución estándar de `pytest` sin necesidad de declarar `PYTHONPATH` manualmente ni en el entorno de CI.
- Añadidos tests `test_pactl_not_found` y `test_pactl_permission_error` en `tests/test_audio_service.py` para cubrir los casos de error `FileNotFoundError` y `PermissionError` que el servicio captura en `run_pactl`.

---

<!-- Plantilla para nuevas versiones:

## [X.Y.Z] - AAAA-MM-DD

### Añadido
-

### Cambiado
-

### Obsoleto
-

### Eliminado
-

### Corregido
-

### Seguridad
-

-->

[Sin publicar]: https://github.com/danuser2018/host-service/compare/HEAD...HEAD
